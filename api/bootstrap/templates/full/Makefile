setup:	if ! git rev-parse --git-dir > /dev/null 2>&1; then \
			echo "Initializing Git repository..."; \
			git init; \
		fi

		if command -v pip &> /dev/null; then \
			pip install -r requirements.txt \
 \
; \
		elif command -v pip3 &> /dev/null; then \
			pip3 install -r requirements.txt \
 \
; \
		else \
			echo "Error: pip and pip3 are not installed"; \
		fi
		
		pre-commit install
		pre-commit install --hook-type commit-msg

format:
		pre-commit run --all-files

clean:
		rm -rf *.egg-info
