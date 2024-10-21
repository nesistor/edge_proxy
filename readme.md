
# LLama proxy.

This project operates as a proxy that analyzes web requests and responses, utilizing Redis to store this data efficiently. It employs the LLaMA model to intelligently set the Time-to-Live (TTL) for infrequent requests, ensuring optimal cache management. Furthermore, the application learns the structure of incoming requests, allowing it to autonomously retrieve current requests in the future and cache them in Redis for improved performance.

## Run Locally

Clone the project

```bash
  git clone https://github.com/nesistor/llama_proxy
```

Go to the project directory

```bash
  cd project
```

Start the server

```bash
  make up_build
```


## License

This project is licensed under the [Creative Commons Attribution-NonCommercial (BY-NC)](https://creativecommons.org/licenses/by-nc/4.0/) License.
