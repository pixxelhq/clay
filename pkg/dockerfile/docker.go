package dockerfile

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/pkg/errors"
)

func buildDockerfile(useHttpRunner bool, PythonVersion string, UseConda bool, UseGdal bool, AptGet []string, Requirements string, OutputFolder string, SourceCodeFolder string, ModelSpecificationPath string) error {
	// Determine base image based on whether to use miniconda
	var baseImage string
	if UseConda {
		baseImage = "continuumio/miniconda3"
	} else {
		baseImage = "python:" + PythonVersion + "-slim"
	}

	// Start building Dockerfile
	dockerfile := "FROM " + baseImage + "\n\n"

	// Copy source code and model specification files to image
	dockerfile += "COPY " + SourceCodeFolder + " /app\n"
	dockerfile += "COPY " + ModelSpecificationPath + " /app\n\n"

	// Set working directory
	dockerfile += "WORKDIR /app\n\n"

	// Install GDAL if needed
	if UseGdal && !UseConda {
		AptGet = append(AptGet, "gdal-bin", "libgdal-dev")
	}

	// Install apt-get packages if needed
	if len(AptGet) > 0 {
		dockerfile += "RUN apt-get update && apt-get install --yes " + strings.Join(AptGet, " ") + "\n\n"
	}

	// Install Python packages from requirements.txt or conda.yml
	if strings.HasSuffix(Requirements, ".txt") {
		if UseConda {
			return errors.Errorf("If you want to use conda, please provide a conda environment file instead.")
		}
		dockerfile += "RUN pip install --no-cache-dir -r " + Requirements + "\n"
	} else {
		if !UseConda {
			return errors.Errorf("If you want to use a conda environment, please set use_conda to `true`")
		}
		dockerfile += "RUN conda env create --file " + Requirements + " && conda clean --all --yes\n"
		dockerfile += "ENV PATH /opt/conda/envs/$(head -1 " + Requirements + " | cut -d' ' -f2)/bin:$PATH\n"
		if UseGdal {
			dockerfile += "RUN conda install --yes gdal\n\n"
		}
	}
	dockerfile += "\n"

	if useHttpRunner {
		// Expose port and start server
		dockerfile += "EXPOSE 8000\n"
		dockerfile += "CMD [\"python3\", \"entry.py\"]\n"
	} else {
		// Start Job runner using ENTRYPOINT
		dockerfile += "ENTRYPOINT [\"python3\", \"entry.py\"]\n"
	}

	// Write Dockerfile to output folder
	dockerfilePath := filepath.Join(OutputFolder, "Dockerfile")
	err := os.WriteFile(dockerfilePath, []byte(dockerfile), 0644)
	if err != nil {
		return err
	}
	return nil
}

func GenerateDockerfile(modelSpecificationPath string, sourceCodeFolder string, useHttpRunner bool) error {
	modelSpecificationPath, err := filepath.Abs(modelSpecificationPath)
	if err != nil {
		return err
	}
	if sourceCodeFolder == "" {
		fmt.Println("No `sourceCodeFolder` provided. Using \"./src\" by default")
	}
	sourceCodeFolder, err = filepath.Abs(sourceCodeFolder)
	if err != nil {
		return err
	}

	build, err := getBuildFromConfigFile(modelSpecificationPath)
	if err != nil {
		return err
	}

	err = buildDockerfile(useHttpRunner, build.PythonVersion, build.Conda, build.Gdal, build.AptGet, build.Requirements, ".", sourceCodeFolder, modelSpecificationPath)
	return err
}
