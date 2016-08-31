Caleydo Data MongoDB ![Caleydo Web Server Plugin](https://img.shields.io/badge/Caleydo%20Web-Server-10ACDF.svg)
=====================

Data provider plugin for loading (graph) data stored in a [MongoDB](https://www.mongodb.com/).

Installation
------------
```bash
./manage.sh clone Caleydo/caleydo_data_mongo
./manage.sh resolve
```

If you want this plugin to be dynamically resolved as part of another application of plugin, you need to add it as a peer dependency to the _package.json_ of the application or plugin it should belong to:

```bash
{
  "peerDependencies": {
    "caleydo_data_mongo": "*"
  }
}
```

Administrating MongoDB from your host machine
------------

Follow this steps if you want to administrate the MongoDB instance that is installed inside the virtual machine (using Vagrant)

1. Download any MongoDB Administration tool (e.g., [RoboMongo](http://www.robomongo.org))
2. Create a new connection, save it, and connect
```
address: localhost
port: 27017
activate use ssh tunnel
SSH address: 127.0.0.1
SSH port: 2222
SSH user name: vagrant
SSH password: vagrant
```


***

<a href="https://caleydo.org"><img src="http://caleydo.org/assets/images/logos/caleydo.svg" align="left" width="200px" hspace="10" vspace="6"></a>
This repository is part of **[Caleydo Web](http://caleydo.org/)**, a platform for developing web-based visualization applications. For tutorials, API docs, and more information about the build and deployment process, see the [documentation page](http://caleydo.org/documentation/).

