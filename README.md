# PigeonHive

PigeonHive is a tool for offensive security teams to simulate MFA-defeating social engineering attacks at scale. 

It defeats MFA by tricking end users into authenticating on an attacker-controlled server. It creates an unlimited number of hive nodes using containerized browsers sharing their content through VNC. This allows security teams to simulate attacks for large groups of end users, using real login portals for phishing campaigns.

# Intro

## The Attack

PigeonHive uses the "Browser-in-the-Middle" (BITM) attack. This was inspired by [original research](https://link.springer.com/article/10.1007/s10207-021-00548-5)[^1] and a [popular implementation](https://mrd0x.com/bypass-2fa-using-novnc/)[^2].

[^1]: https://link.springer.com/article/10.1007/s10207-021-00548-5 - An academic look at the attack
[^2]: https://mrd0x.com/bypass-2fa-using-novnc/ - The original inspiration for this repository

The attack works by hosting an isolated browser instance in an attacker-controlled network. This browser instance can point to any login page. This instance is also running a VNC server, which is connected to by a client running in the victim's browser. By doing this, the victim is actually interacting with the *real* login page, just on a different computer.

## How PigeonHive Makes This Useful

PigeonHive takes this technique and makes it operational in a few ways.

1. Containerizes the browser/VNC combo machine (this is called a "pigeoncell")
2. Makes it easy to map these machines to email addresses for internal tracking
3. Allows for accessing each machine through subdomains
4. Enables interaction tracking (currently in the "GoPhish Addon" branch)

# Usage

## Setup

### Prerequisites
* You must be running a Docker Swarm
  - This is possible even if you only have one node - please refer to [Docker's documentation on how to create a Swarm](https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/)
* Ensure that your desired manager node has the label "pigonhive_leader=true"
  - `docker node update --label-add pigeonhive_leader=true node_name_here`

### Installation
Install requirements with

`pip install -r requirements.txt`

## Running
To run PigeonHive and see the *help* output, run

`python3 pigeonhive.py -h`

PigeonHive features three subcommands: **create**, **query**, and **delete**.

### Subcommands

#### create

Creates pigeoncell containers and exposes them to the reverse proxy.

#### query

Allows you to list active pigeoncell containers and see their email mappings.

#### delete

Removes active containers

# The Name

The name PigeonHive was chosen because this method essentially creates pigeonholes for the targeted users. "Hive" seemed appropriate for a group of these managed by a swarm.
