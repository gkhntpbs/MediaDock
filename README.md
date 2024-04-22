![Logo](https://raw.githubusercontent.com/gkhntpbs/MediaDock/main/app/MediaDock.ico)
# Media Dock

This project uses Docker Compose to manage several services (Jellyseerr, Sonarr, Radarr, Prowlarr, qBittorrent, and an OpenVPN client) running on Docker. These services work together to download, manage, and stream media files. It's important to note that Jellyfin is not included in this stack and needs to be set up separately as it runs directly on the host machine.

## Getting Started

This guide explains how to launch and configure the project on your local machine.

### Prerequisites

Before running the project, ensure Docker and Docker Compose are installed on your system. You can find installation instructions for Docker at the [official Docker documentation](https://docs.docker.com/get-docker/). For Docker Compose, follow [this guide](https://docs.docker.com/compose/install/).

Additionally, clone this repository to have the necessary files on your local machine.

### Installation

After cloning the repository, navigate to the application directory and run the `MediaDock.exe` executable to set up and start the Docker containers. This executable ensures all services are running and applies any necessary updates automatically.

### Configuration

Edit the service settings in the `docker-compose.yml` file to tailor the project to your needs. Specify the necessary configuration files and persistent data stores (volumes) for each service in this file.

**Initial Service Configuration:**
After the installation, each service may require a one-time configuration to tailor the settings to your needs. You will need to access each service's web interface to configure options such as network settings, download folders, and integration with other services.

### Automatic Updates

If you wish for MediaDock to automatically check for updates and maintain the containers, add `MediaDock.exe` to your system's startup programs. This will ensure the services are always up-to-date upon system boot.

**Note:** `MediaDock.exe` is currently in alpha and is not required to run the services directly from Docker Compose.

### Services Explained

#### Jellyseerr
A web interface for managing requests for your media library. Jellyseerr is essential for handling user requests and integrating them with other media management tools like Sonarr and Radarr.

#### Sonarr
An automated TV series management tool. Sonarr can monitor multiple RSS feeds for new episodes of your favorite shows and automate the downloading process. It can also manage your media library by renaming and organizing episodes into seasons.

#### Radarr
Similar to Sonarr, but for movies. Radarr automates the process of searching for movies that are available as torrents or Usenet downloads and can integrate with download clients to automate your movie download workflow.

#### Prowlarr
A search indexer for Usenet and torrents. Prowlarr supports integration with multiple download clients and can be used to manage and automate your content acquisition strategies.

#### qBittorrent
A powerful and open-source torrent client. It is used to download media files from torrents and integrates directly with Sonarr, Radarr, and Prowlarr for seamless media management.

#### OpenVPN Client
Used to securely connect to the internet, protecting your privacy and enabling safe downloads. It's crucial for ensuring that your downloads are secure and private.

### Starting Up

Follow these steps to start the project:

1. Open the command line.
2. Go to the project directory.
3. Run the following command to start all services:
docker-compose up -d
4. To check that all services are running properly, use:
docker-compose ps

## Usage

This setup uses the following ports to access the services:

- Jellyseerr: 5055
- Sonarr: 8989
- Radarr: 7878
- Prowlarr: 9696
- qBittorrent: 8080

You can access the web interface of each service through these ports in your browser, for example, "http://localhost:5055/".

## Contributing

If you would like to contribute to the project, please open an issue to discuss your ideas before submitting a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
