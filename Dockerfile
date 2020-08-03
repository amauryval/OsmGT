FROM continuumio/miniconda3

# for graphtool
RUN apt-get update
RUN apt install libgtk-3-0 libgtk-3-dev -y

# prepare app directory
COPY environment.yml /home/app/
WORKDIR /home/app/

# conda env creation
RUN conda env create -f environment.yml
RUN echo "source activate osmgt" > ~/.bashrc
ENV PATH /opt/conda/envs/osmgt/bin:$PATH
#RUN echo "source activate $(head -1 $conda_dir_env | cut -d' ' -f2)" > ~/.bashrc
#ENV PATH /opt/conda/envs/$(head -1 $conda_dir_env | cut -d' ' -f2)/bin:$PATH

COPY . /home/app/

EXPOSE 8888
RUN jupyter notebook --generate-config --allow-root
CMD ["conda", "run", "-n", "osmgt", "jupyter", "notebook", "--allow-root", "--notebook-dir=.", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--NotebookApp.token=''"]
