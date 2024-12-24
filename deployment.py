from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import subprocess
from typing import TypedDict


with open(".env", "r") as f:
    for line in f:
        if "DEPLOYMENT_TOKEN" in line:
            deployment_token = line.strip().split('=')[1]
if not deployment_token:
    print('Deployment token not found in .env file', flush=True)
    exit(1)


app2compose = {
    "backend": "compose.backend.yaml",
    "frontend": "compose.frontend.yaml",
}


class DockerImage(TypedDict):
    image: str
    compose_file: str
    env_variable: str


class DeploymentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if '/deployment' in self.path:
            self.handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def handle_deploy(self):
        param_dict = self.get_query_params()
        if param_dict.get("token") != deployment_token:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return

        if param_dict.get("app") not in app2compose:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid application')
            return

        app = param_dict["app"]
        body = json.loads(self.rfile.read(
            int(self.headers['Content-Length'])))
        image = body["repository"]["repo_name"] + \
            ":" + body["push_data"]["tag"]

        with open('docker_images.json', 'r') as f:
            images: dict[str, DockerImage] = json.load(f)
            images[app]["image"] = image
        with open('docker_images.json', 'w') as f:
            json.dump(images, f, indent=2)
        deploy_image(images[app])

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Deployment request received')

    def get_query_params(self) -> dict:
        if '?' not in self.path:
            return {}
        query = self.path.split('?')[1]
        param_dict = {}
        for param in query.split('&'):
            key, value = param.split('=')
            if key in param_dict:
                if isinstance(param_dict[key], list):
                    param_dict[key].append(value)
                else:
                    param_dict[key] = [param_dict[key], value]
            else:
                param_dict[key] = value
        return param_dict


def run(server_class=HTTPServer, handler_class=DeploymentHandler, port=5000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting http server on port {port}', flush=True)
    httpd.serve_forever()


def deploy_image(image: DockerImage):
    # set image as environment variable
    os.environ[image['env_variable']] = image['image']
    try:
        subprocess.run(['docker', 'compose', '-f', image['compose_file'],
                        'down'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f'Error occurred during docker-compose up: {e.stderr}', flush=True)
        return
    try:
        subprocess.run(['docker', 'compose', '-f', image['compose_file'],
                        'up', '-d'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f'Error occurred during docker-compose up: {e.stderr}', flush=True)
        return
    print('Docker Compose triggered successfully', flush=True)


if __name__ == '__main__':
    run()
