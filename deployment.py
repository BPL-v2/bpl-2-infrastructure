from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import subprocess
import cgi


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

        print('Received deployment request', flush=True)
        body = json.loads(self.rfile.read(
            int(self.headers['Content-Length'])))
        print(f'Body: {body}', flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Deployment request received')

        # ctype, pdict = cgi.parse_header(self.headers['content-type'])
        # pdict['boundary'] = pdict['boundary'].encode('ascii')
        # if ctype == 'multipart/form-data':
        #     fields = cgi.parse_multipart(self.rfile, pdict)
        #     if 'image' in fields and fields.get("app", [None])[0] in app2compose:
        #         image_data = fields['image'][0]
        #         with open('docker_image.tar', 'wb') as f:
        #             f.write(image_data)
        #         print('Docker image saved to docker_image.tar', flush=True)
        #         deploy_image(app2compose[fields['app'][0]])
        #         os.remove('docker_image.tar')
        #         self.send_response(200)
        #         self.end_headers()
        #         self.wfile.write(
        #             b'Docker image loaded and Docker Compose triggered')
        #     else:
        #         self.send_response(400)
        #         self.end_headers()
        #         self.wfile.write(b'Invalid data')
        # else:
        #     self.send_response(400)
        #     self.end_headers()
        #     self.wfile.write(b'Invalid content type')

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


def deploy_image(compose_file: str):
    try:
        result = subprocess.run(
            ['docker', 'load', '-i', 'docker_image.tar'], check=True, capture_output=True, text=True)
        print(f'Docker load output: {result.stdout}', flush=True)
    except subprocess.CalledProcessError as e:
        print(f'Error occurred during docker load: {e.stderr}', flush=True)
        return
    print('Docker image loaded successfully', flush=True)

    try:
        result = subprocess.run(['docker', 'compose', '-f', compose_file,
                                'down'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f'Error occurred during docker-compose up: {e.stderr}', flush=True)
        return
    try:
        result = subprocess.run(['docker', 'compose', '-f', compose_file,
                                'up', '-d'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f'Error occurred during docker-compose up: {e.stderr}', flush=True)
        return
    print('Docker Compose triggered successfully', flush=True)


if __name__ == '__main__':
    run()
