FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .
RUN sed -i '/prefix:/d' environment.yml
RUN conda env create -f environment.yml

COPY .env tars.json ./

COPY . .

# Install project as editable package for proper imports
RUN conda run -n agentes_ia pip install -e .

EXPOSE 8000

# Start Uvicorn
CMD ["conda", "run", "--no-capture-output", "-n", "agentes_ia", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]