# HZZ ATLAS ANALYSIS
## Description

In this repository I leverage cloud-based technologies to enhance the data processing capacity of the ATLAS HZZ Analysis notebook.
I refactor the original script to construct 5 docker containers. There are 4 containers are dedicated to data processing the simulated background datasets and signal datasets along with
the collision data. There's a 5th container dedicated to plotting the processed data.

The processing containers work in-parralel and sequentially transfer the processed data to the plotting container using RabbitMQ to produce the histogram plot.
Communication via containers is achieved using RabbitMQ.

## Running Container Cluster

To run the container clusters, simply navigate to the directory you've cloned this repository to in your console and enter the following command:
`docker-compose build`

## Using Docker Swarm to Scale

To scale the analysis you can use docker swarm.

(1) Initiliasing Docker Swarm

`docker swarm init --advertise-addr <IP-ADDRESS>`
