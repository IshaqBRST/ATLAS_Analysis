# HZZ ATLAS ANALYSIS
## Description

In this repository I leverage cloud-based technologies to enhance the data processing capacity of the ATLAS HZZ Analysis notebook.
I refactor the original script to construct 5 docker containers. There are 4 containers are dedicated to data processing the simulated background datasets and signal datasets along with
the collision data. There's a 5th container dedicated to plotting the processed data.

The processing containers work in-parralel and sequentially transfer the processed data to the plotting container using RabbitMQ to produce the histogram plot.
Communication via containers is achieved using RabbitMQ.

## Running Container Cluster

To run the container clusters, simply navigate to the directory you've cloned this repository to in your console and enter the following command:
```docker-compose build```

## Using Docker Swarm to Scale

To scale the analysis you can use docker swarm.

### Initiliasing Docker Swarm

You will need to initialise docker swarm by starting a manager node. This command converts the docker engine into a swarm manager node.
The IP address you specifiy should be an IP address or a network interface that other nodes can reach.

`docker swarm init --advertise-addr <IP-ADDRESS>`

### Additional Manager Nodes

Additional nodes may be added to the swarm as manager nodes through the following command.

`docker swarm join-token manager`

### Additional Nodes

Additional nodes may be added to the swarm as worker nodes through the following command.

`docker swarm join --token <TOKEN-NUMBER> <IP-ADDRESS:PORT-EXPOSED>`

### Replicating Services/Containers

When using Docker Swarm, utilise the 'docker-compose-swarm.yml' file found in the repository instead. This is because you will need to state how many replicas of each service there are within the swarm. This compose file has been modified to serve as a template when deploying the containers using Docker Swarm. 

### Deploying Docker Swarm

Use the following command to deploy the stack to Docker Swarm. Replace 'myapp' with preferred stack name. 

`docker stack deploy -c docker-compose.yml myapp`

### Adjusting Services Based on Load from Console

You can use the following command to adjust the number of replica services using this command

`docker service scale myapp_web=4`

For example, you can using `docker service scale myapp_signal_data_processor=5` will create 5 additional containers to process the signal_data , thereby facilitating up-scaling.







