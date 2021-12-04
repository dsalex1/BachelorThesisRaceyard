 # Information - MIP

These are the collected information for working at the multimedia information processing group. Please read this document carefully for the general information about working with us on your thesis or project. The document will explain general information about these topics and about working with our servers and computers.

Throughout this document, the supervisor is the member of MIP which guides you mainly.  You are referenced as student.

## General

If you work with us, please contact us immediately if you have questions, issues or recommendations. As supervisors we want to help you and we will always do our best to help you if it possible. The most important message you should take away from this document is : **SPEAK TO US** Only if we know of a question or issue we can help. As long as you don't insult us we will certainly help you.

Most likely you will work with us for the next six months and you will have about weekly meetings with your supervisor. For most elements we do not have formal requirements so please see your supervisor for details.

### Thesis (Bachelor / Master)

You should meet with your supervisor to discuss the topic and get an introduction to the topic. After your initial introduction you have to register the thesis with the office. You have to apply for an thesis at the examination office and only after that we will receive the papers to fill in your topic and supervisors.

Then you will have about 6 months for w**orking on the topic, writing your thesis and making a presentation**.

You should work for about four months mainly on the topic and then mainly write two months. This means you should also start writing in the first months and still have to evaluate some experiments in the last two months. You should aim at **finishing writing the introduction and basics at the end of the first four months.** Your main source code should also work at this point.

Your thesis should be around 20-40 pages but up to 100 pages might also be okay. **We care more about content than page numbers.** Write all the required details while being precise. Support your work with graphics and illustrations. We will guide you during the process so you will get a feeling where you need more and where you have sufficient content. Roughly speaking the content should be a third introduction + basics, a third methods and a third evaluation + discussion. Hand in early drafts to your supervisor to get feedback and understand what is important to your supervisor. 

**General tips:** 

- Be precise, don't say magnificent improvements rather say an improvement of 20%
- Proof every claim by explanation or reference
- Be positive about your work, don't state we tried but it is not good enough
- Don't copy without referencing. Do it and you will automatically fail!!
- Give good illustrations and write captions to understand them
- Check your reading flow and spelling



The presentation will be in the end of the semester and will be publicly available. You can visit the presentation of other students for a first impression. Discuss the presentation before hand with your supervisor. In general, **make a presentation about your content which is**

- interesting to the audience 
- gives an overview about your work
- shows your results
- easily to understand

**Avoid**:

-  overflowing slide
-  too many slides (about one per minute is often sufficient)
- large formulas (if you do not explain them in detail)
- too many tables (you can't explain all results)
- only slides with images (only images are not enough)
- only slides with text (images help to visualize the content)

Additionally, train your speech and be confident and certain about your presentation. You should speak freely and to the audience. **TRAIN YOUR SPEECH!!!** Just to be sure train your speech it is really important.

###### Difference Bachelor vs. Master

The bachelor thesis has to be written parallel to the semester. The master thesis is six months after the start. A master thesis should provide more novelty than a bachelor thesis and some minor formal details like the lengths of the presentations are different. Please see the official documents for this. A bachelor thesis is 15 ECTS so about half of your week (20h) you should spend on this project. A master thesis is about 30 ECTS thus you should spend your complete week (40h) on this topic.

### Project

**A master project is similar to a thesis if you dropped the writing of a thesis.** The presentation is optionally but we often ask you to do a presentation anyway for our colleagues. 

At the end of a master project you have to write a report of 10-20 pages. This document should give an overview about the project and what you have done and tried. This is the main document we will hand the next students to continue your work so write it to be helpful to an unexperienced users like you were at the beginning of your project. Follow the general guidelines for the writing and the presentation as described above. **We care more about content than page numbers or formats.** If you can make a brilliant report in 5 or only 30 pages that's fine. Ask your supervisor for guidance.

A master project is about 10 ECTS and thus you should spend a third of your week (14h) on this topic.



## Working with our hardware

First of all, you need an MIP account and password. Please ask your supervisor if you should contact Torge Storm (tost@informatik.uni-kiel.de) directly or the supervisor contacts him.

You can work directly on PCs in our lab in Room 304 or you can login remotely via Thinlinc.

### Sidenote: ThinLinc

This section only applies to remote login. Download the Thinlinc Client and connect to the server `file.mip.informatik.uni-kiel.de` via your username and password. 

**WARNING**: Due to Firewall restrictions and multiple simultaneously instantiated connections by Thinlinc you will be banned one failed login attempt for several hours. If you get a time out error you are most likely banned. It should normally automatically work in a few hours (3-4h). For any further issues please contact your supervisor.

**IMPORTANT:** Always log out the user in ThinLinc. We have shared license and you might block other users if you do not log out. 

### PC Structure

Each PC has a name which is normally the name of a river. The most important names for you are `treene`, `trave` and `ems`. You should normally start on one of these PCs. Our GPU Servers are `lena`and `amur`. You can switch between pcs via `ssh <PC  NAME>`. Keep to your assigned PC if you have to discussed it differently with your supervisor.

Your home directory is `/home/<USERNAME>/` and is shared across all our working stations. Do not store large amounts of data (> 500MB) in your home directory. It is daily backuped and it would flood the hard drives. Use your data directory for large data (see below). 

Your data directory can be found at `/data1/<USERNAME>`. This folder has to manually created and thus please contact your supervisor if it is not available. This directory is not shared but you can access it via `/datapc/<PC NAME>/<USERNAME>` from any other pc. 

### Running code

You do not have root privileges but you are allowed to run any code as long as it does not harm other users or the environment. We recommend using docker for a better separation of working spaces. Normally you can not run docker commands (you would need root privileges) thus we created a special `mip-docker-run` command. Futhermore, if you want to work on the GPU servers please do not just run your code in docker but schedule your job in a queue with `with_gpu`.

#### mip-docker-run

You can run a docker container with the following command. You are able to execute this one command with elevated privileges. 

```
# general
sudo mip-docker-run <OPTIONAL mip-docker-run ARGS> <IMG NAME> <COMMAND INSIDE DOCKER CONTAINER>

# example 
sudo mip-docker-run --rm --gpus '"device=0"' nvidia/cuda:10.2-base nvidia-smi
```

The optional `mip-docker-run ARGS` can be:

- `--rm` automatically removes the container on container exit
- `--gpus` pass a GPU demand to the docker file, see the original documentation for formatting informations

Inside the container you will have your MIP Account privileges, UID and GID. The working directory from where you executed the command will be mounted under `/src` and your data directory on the current PC under `/data`.

You can not build the desired docker image on your own. Please define a Dockerfile https://docs.docker.com/engine/reference/builder/ and ask your supervisor to build it with 

```
# building than tagging
docker build .
docker tag <IMAGE_ID> <NAME>

# or direct tagging
docker build -t <NAME> .
```



#### with_gpu

This command allows you to enque a job into the pipeline on GPU server.

```
# general structure
with_gpu -n <NUM GPUS> sudo mip-docker-run <OPTIONAL mip-docker-run ARGS> --gpus '"device=$CUDA_VISIBLE_DEVICES"' <IMG NAME> <COMMAND INSIDE DOCKER CONTAINER>

# example to check if you get an GPU
with_gpu -n 1 sudo mip-docker-run --rm --gpus '"device=$CUDA_VISIBLE_DEVICES"' nvidia/cuda:10.2-base nvidia-smi
```

Do not modify the gpus arguments because it will be automatically set. **WARNING:** As long as you use sudo you need to type in your password when your job is scheduled. If this is an issue e.g. because you want to run multiple runs over night please contact your supervisor. The following additional elements are copied from the tool README.md avaiable to all supervisors.

###### Client Application

The client application will ask the daemon for one or multiple free GPUs, set `CUDA_VISIBLE_DEVICES` accordingly and run the supplied command.
The command can be any shell command.
The command is executed with the rights of the user e.g. a docker command can only be executed by root, sudoer or docker group members.

    $ with_gpu -n <NUM_GPUS> <COMMAND WITH ARGS>
    $ with_gpu -n 3 docker run --gpus "'device=$CUDA_VISIBLE_DEVICES'" -it --rm nvidia/cuda:10.2-base nvidia-smi -L
    
    > Executing `docker run --gpus device=GPU-7b4c3c45-8c34-85d3-930f-749a60410528 -it --rm nvidia/cuda:10.2-base nvidia-smi -L` with CUDA_VISIBLE_DEVICES=GPU-7b4c3c45-8c34-85d3-930f-749a60410528...
    > GPU 0: GeForce RTX 2080 Ti (UUID: GPU-7b4c3c45-8c34-85d3-930f-749a60410528)

**WARNING:**  When using `CUDA_VISIBLE_DEVICES` in the command line, make sure to enclose it in escaped double quotes and single quotes (`"'device=$CUDA_VISIBLE_DEVICES'"`, like in the above example)
    so that the it does not get replaced by the shell before passing it to `with_gpu`. The outer double quotes are `required <https://github.com/docker/docker.github.io/issues/11010>`_ by docker.


If you want to run the mip-docker-run command to execute a docker container you can use the command as follows

    $  with_gpu -n <NUM GPUS> sudo mip-docker-run <OPTIONAL mip-docker-run ARGS> --gpus '"device=$CUDA_VISIBLE_DEVICES"' <IMG NAME> <COMMAND IN DOCKER>
    $  with_gpu -n 1 sudo mip-docker-run --rm --gpus '"device=$CUDA_VISIBLE_DEVICES"' nvidia/cuda:10.2-base nvidia-smi

**WARNING:** As long as you use sudo you need to type in your password on scheduling.


If for any reason you can not run your command with the given interface, you can make a dummy request as seen below.

    $ with_gpu -n 1 sleep infinity

**WARNING:**  This command is not freeing the resources itself. You as the user have to manually abort the command. This way of using the queue is contradicting the general idea. As a user you are blocking all other users from using the resources. Use this dummy request carefully and only if you know what you are doing.

###### Additional arguments

The arguments are sorted roughly in the order of priority.
This means the lower an item in this list the fewer it should be used.

- *n-gpus* - Number of gpus requested, should always be used or defaults to 1
- *name* - Name of the request, the name is not required but should always be provided for better readability of the queue.
- *info* - Shows information about the queue. The more often i or info is given the higher the verbosity. If you want to understand when and why your job is scheduled or most likely be scheduled check this parameter. No additional arguments need to be provided.
- *timeout* - Set a timeout for waiting of the requested resources. Default Infinity

###### User Queue Description

The user queues aims at treating each user equally based on their used gpu hours.
The queue sorts the jobs based on 4 markers, the user score, the utilization, skipping and fulfillment.
All these values can be checked by running ``with_gpu -iii``.
Based on the sorting the first fitting job (enough free gpus for the request) is scheduled.

The user score is the temporal used gpu hours (U) minus the temporal waiting time (W).
The overall usage (O) is just given for reference.
The temporal scores are calulated based on the time and gpus for which the user used or waited on the resources.
They are temporal as they decrease over time. E.g. as long a user is only using one gpu their using scores is not even increasing.
The scores are sorted in ascending order.

The utilization is the absolute difference between the free gpus and the needed resources for the request.
In order to maximize the utilization large jobs are preferred and jobs with more missing resources.
The utilization is sorted in descending order.

Any job based on the above sorting can be skipped if a certain waiting time (e.g. 12 hours) is not surpassed.
We need to skip jobs to allow a high utilization and the time constraint prevents starvation.

Fulfillment is defining if the request can be fullfilled.
For example if the resources are used by external tasks outside the queue, the request might not be fullfillable with all available gpus to the scheduler.
These tasks are always executed last as they may cause almost infinite waiting.

