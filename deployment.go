package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"time"

	"github.com/joho/godotenv"
)

type WebhookRequest struct {
	CallbackUrl string `json:"callback_url"`
	PushData    struct {
		PushedAt int    `json:"pushed_at"`
		Pusher   string `json:"pusher"`
		Tag      string `json:"tag"`
	} `json:"push_data"`
	Repository struct {
		CommentCount    int    `json:"comment_count"`
		DateCreated     int    `json:"date_created"`
		Description     string `json:"description"`
		Dockerfile      string `json:"dockerfile"`
		FullDescription string `json:"full_description"`
		IsOfficial      bool   `json:"is_official"`
		IsPrivate       bool   `json:"is_private"`
		IsTrusted       bool   `json:"is_trusted"`
		Name            string `json:"name"`
		Namespace       string `json:"namespace"`
		Owner           string `json:"owner"`
		RepoName        string `json:"repo_name"`
		RepoUrl         string `json:"repo_url"`
		StarCount       int    `json:"star_count"`
		Status          string `json:"status"`
	} `json:"repository"`
}

type DockerImage struct {
	Tag        string     `json:"tag"`
	app        string     `json:"compose_file"`
	Repository string     `json:"repository"`
	Timestamp  *time.Time `json:"timestamp"`
}
type DockerImageOut struct {
	Tag        string    `json:"tag"`
	Repository string    `json:"repository"`
	Timestamp  time.Time `json:"timestamp"`
}
type DockerImages []DockerImage
type DockerImagesOut []DockerImageOut

func (images *DockerImages) MarshalJSON() ([]byte, error) {
	imagesOut := make(DockerImagesOut, 0)
	for _, image := range *images {
		if image.Timestamp != nil {
			imagesOut = append(imagesOut, DockerImageOut{
				Tag:        image.Tag,
				Repository: image.Repository,
				Timestamp:  *image.Timestamp,
			})
		}
	}
	return json.Marshal(imagesOut)
}

var images = DockerImages{
	{
		Repository: "liberatorist/bpl2-backend",
		Tag:        "",
		app:        "backend",
		Timestamp:  nil,
	},
	{
		Repository: "liberatorist/bpl2-frontend",
		Tag:        "",
		app:        "frontend",
		Timestamp:  nil,
	},
}

func postDeploymentHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Query().Get("token") != os.Getenv("DEPLOYMENT_TOKEN") {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	body := WebhookRequest{}
	err := json.NewDecoder(r.Body).Decode(&body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	for i, image := range images {
		if image.Repository == body.Repository.RepoName {
			image.Tag = body.PushData.Tag
			now := time.Now()
			image.Timestamp = &now
			err := deployImage(image)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			images[i] = image
			w.Write([]byte("Deployment successful"))
			return
		}
	}
	http.Error(w, "Unknown repository", http.StatusBadRequest)
}

func deploymentHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		postDeploymentHandler(w, r)
		return
	}
	if r.Method == "GET" {
		imagesJson, err := images.MarshalJSON()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write(imagesJson)
		return
	}
	http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
}

func runShellCommand(command ...string) error {
	cmd := exec.Command(command[0], command[1:]...)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		return fmt.Errorf("error occurred during %v: %v", command, stderr.String())
	}
	return nil
}

func deployImage(image DockerImage) error {
	os.Setenv("IMAGE", image.Repository+":"+image.Tag)
	err := runShellCommand("docker", "pull", image.Repository+":"+image.Tag)
	if err != nil {
		return err
	}
	err = runShellCommand("docker", "compose", "-f", image.app+"/docker-compose.yaml", "down")
	if err != nil {
		return err
	}
	err = runShellCommand("docker", "compose", "-f", image.app+"/docker-compose.yaml", "up", "-d")
	if err != nil {
		return err
	}
	return nil
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}
	http.HandleFunc("/deployment", deploymentHandler)

	err = http.ListenAndServe(":5000", nil)
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}

}
