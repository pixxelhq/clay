package block

import (
	"context"
	"errors"
	"fmt"
	"os"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/api/block"
	"github.com/example/clay/cmd/common"
	"github.com/example/clay/pkg"
	"github.com/spf13/cobra"
)

func GetBlockCmd() *cobra.Command {
	var (
		env          string
		blockName    string
		blockVersion string
		status       string
		err          error
	)

	cmd := &cobra.Command{
		Use: "block",

		Short: "Get spec file of a block version",

		Long: heredoc.Doc(`
    		Get spec file of a block version.
			By Default only "released" block spec is provided.
			Set "status" flag to fetch "draft" and "disabled" block spec
			`),

		PreRunE: func(cmd *cobra.Command, args []string) error {

			blockVersion, err = cmd.Flags().GetString("version")
			if err != nil {
				return err
			}

			blockName, err = cmd.Flags().GetString("name")
			if err != nil {
				return err
			}
			status, err = cmd.Flags().GetString("status")
			if err != nil {
				return err
			}

			env, err = cmd.Flags().GetString("env")
			if err != nil {
				return err
			}
			_, err = ParseStatusOptions(status)
			if err != nil {
				return err
			}
			_, err = ParseEnvOptions(env)
			if err != nil {
				return err
			}
			if blockVersion != "" && !common.IsValidVersion(blockVersion) {
				return errors.New("invalid version syntax. Follow semVer pattern eg. v0.0.1")
			}

			return nil
		},

		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.TODO()
			logger := common.Getlogger()

			if blockName == "" || blockVersion == "" {
				return errors.New("provide valid block name and version. Use list block cmd to list available blocks,if needed")
			}

			var specData []byte
			specData, err = block.GetBlock(ctx, logger, blockName, blockVersion, env, status)
			if err != nil {
				return err
			}
			if specData == nil {
				fmt.Println("No block found for the given details")
				return nil
			}

			fmt.Println("Spec file for version:", blockVersion)
			fmt.Println(string(specData))
			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&blockVersion, "version", "v", "", "Version of block")
	cmd.Flags().StringVarP(&status, "status", "s", "released", "Status of block: draft, released, disabled")
	return cmd
}

func ListBlockCmd() *cobra.Command {
	var (
		env       string
		blockName string
		status    string
		err       error
		blocks    block.BlockSpec
	)
	cmd := &cobra.Command{
		Use: "block",

		Short: "List blocks ",

		Long: heredoc.Doc(`
		List the blocks available in database.
		If blockname is provided, all available "released" blocks will be listed.
		Use flags to list versions available for a block
		Use flags to list block based on their status.
		`),

		PreRunE: func(cmd *cobra.Command, args []string) error {
			status, err = cmd.Flags().GetString("status")
			if err != nil {
				return err
			}
			blockName, err = cmd.Flags().GetString("name")
			if err != nil {
				return err
			}
			env, err = cmd.Flags().GetString("env")
			if err != nil {
				return err
			}

			_, err = ParseStatusOptions(status)
			if err != nil {
				return err
			}
			_, err = ParseEnvOptions(env)
			if err != nil {
				return err
			}
			return nil
		},

		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.TODO()
			logger := common.Getlogger()

			if blockName == "" {
				blocks, err = block.ListBlock(ctx, logger, env, status)
				if err != nil {
					fmt.Println(err)
					return err
				}

				fmt.Printf("Blocks available in %s as %s:\n", env, status)
				fmt.Printf("%-30s %-20s\n", "Name", "Version")
				for _, block := range blocks.Data {
					fmt.Printf("%-30s %-20s\n", block.Spec.Name, block.Spec.Version)
				}

				return nil
			}

			blocks, err = block.ListVersion(ctx, logger, blockName, env, status)
			if err != nil {
				fmt.Println(err)
				return err
			}

			fmt.Println(status, "version for", blockName)
			for _, block := range blocks.Data {
				fmt.Println("v", block.Spec.Version)
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&status, "status", "s", "released", "Possible status of block: draft, released, disabled")
	return cmd
}

func AddBlockCmd() *cobra.Command {
	var (
		env string
		err error
	)

	cmd := &cobra.Command{
		Use: "block [specFilePath]",

		Short: "Add a new block in Pixxel Labs ",

		Long: heredoc.Doc(`
				Add a new block in Pixxel Labs.
				A block, with the specification file, will be added to Pixxel Lab.
				It will be provided as a drag-and-drop feature to the users.
				`),

		Args: cobra.ExactArgs(1),

		PreRunE: func(cmd *cobra.Command, args []string) error {

			_, err = os.Stat(args[0])

			if os.IsNotExist(err) {
				fmt.Println("File does not exist")
			}

			env, err = cmd.Flags().GetString("env")
			if err != nil {
				return err
			}
			_, err = ParseEnvOptions(env)
			if err != nil {
				return err
			}
			return nil
		},

		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.TODO()
			logger := common.Getlogger()

			specFilePath := args[0]

			env, err = cmd.Flags().GetString("env")
			if err != nil {
				return err
			}
			err = block.PostNewBlock(ctx, logger, specFilePath, env)
			if err != nil {
				return err
			}
			return nil
		},
	}
	return cmd
}

func UpdateBlockCmd() *cobra.Command {

	var (
		env          string
		blockName    string
		blockVersion string
		status       string
		err          error
	)
	cmd := &cobra.Command{
		Use: "block [specFilePath]",

		Short: "Update an existing block in Pixxel Labs ",

		Long: heredoc.Doc(`
			Update an existing block through CLI.
			Specify the blockname, version and updated specfile path to update the block.
			Use flag 'env' to specify the environment in which the block is to be updated.
			`),
		Args: cobra.ExactArgs(1),

		PreRunE: func(cmd *cobra.Command, args []string) error {

			_, err = os.Stat(args[0])

			if os.IsNotExist(err) {
				fmt.Println("File does not exist")
			}

			blockVersion, err = cmd.Flags().GetString("version")
			if err != nil {
				return err
			}

			blockName, err = cmd.Flags().GetString("name")
			if err != nil {
				return err
			}
			status, err = cmd.Flags().GetString("status")
			if err != nil {
				return err
			}

			env, err = cmd.Flags().GetString("env")
			if err != nil {
				return err
			}
			_, err = ParseStatusOptions(status)
			if err != nil {
				return err
			}
			_, err = ParseEnvOptions(env)
			if err != nil {
				return err
			}
			if blockVersion != "" && !common.IsValidVersion(blockVersion) {
				return pkg.ErrInvalidValue("invalid version syntax. Follow semVer pattern eg. v0.0.1")
			}
			if err != nil {
				return err
			}
			return nil
		},

		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.TODO()
			logger := common.Getlogger()

			specFilePath := args[0]

			if blockVersion == "" {
				return errors.New("provide valid version. Use list block cmd to list available block versions,if needed")
			}
			err = block.UpdateBlock(ctx, logger, blockName, blockVersion, specFilePath, env, status)
			if err != nil {
				return err
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&blockVersion, "version", "v", "", "Version of block")
	cmd.Flags().StringVarP(&status, "status", "s", "released", "Status of block: draft, released, disabled")

	return cmd
}
