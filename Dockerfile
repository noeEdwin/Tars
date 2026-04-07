FROM continuumio/miniconda3

WORKDIR /app

# Copy the environment file
COPY environment.yml .

# Remove hardcoded prefix from environment.yml to avoid path issues
RUN sed -i '/prefix:/d' environment.yml

# Create the conda environment
RUN conda env create -f environment.yml

# The rest of the files
COPY . .

# We need to expose port 8000
EXPOSE 8000

# Start Uvicorn
CMD ["conda", "run", "--no-capture-output", "-n", "agentes_ia", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
