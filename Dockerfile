FROM continuumio/miniconda3

# for graphtool
RUN apt-get update
RUN apt install libgtk-3-0 libgtk-3-dev -y

# prepare env file directory
ARG temp_dir=/tmp
ARG conda_file_env=environment.yml
ARG conda_dir_env=$temp_dir/$conda_file_env

COPY $conda_file_env $conda_dir_env
WORKDIR $temp_dir

# conda env creation
RUN conda env create -f $conda_dir_env
RUN echo "source activate osmgt" > ~/.bashrc
ENV PATH /opt/conda/envs/osmgt/bin:$PATH

# copy the library
COPY . /home/app/

WORKDIR /home/app/

RUN conda install --yes pytest pytest-cov

EXPOSE 8888
RUN jupyter notebook --generate-config --allow-root
CMD ["jupyter", "notebook", "--allow-root", "--notebook-dir=.", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
