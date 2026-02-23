#!/bin/bash

# Local .bashrc for this repository
# This file contains project-specific bash configurations

# Add LM Studio to PATH for this project (here's mine)
#export PATH="$PATH:/c/Users/tmf77/.lmstudio/bin"
#alias lms='/c/Users/tmf77/.lmstudio/bin/lms.exe'

#export PATH="$PATH:/c/Users/tmf77/AppData/Local/Programs/Ollama"
#alias ollama='/c/Users/tmf77/AppData/Local/Programs/Ollama/ollama.exe'

# Add R to your Path for this project (here's mine)
export PATH="$PATH:/usr/local/bin"
alias Rscript='Rscript'
# Add R libraries to your path for this project (here's mine)
export R_LIBS_USER="/Library/Frameworks/R.framework/Versions/4.5-arm64/Resources/library"

# Add Python to your Path for this project (here's mine)
export PATH="$PATH:/usr/local/bin"
alias python='python3'

# Add uvicorn to your Path for this project - if using Python for APIs (here's mine)
export PATH="$PATH:/c/Users/tmf77/AppData/Roaming/Python/Python312/Scripts"

echo "✅ Local .bashrc loaded."