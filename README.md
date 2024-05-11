
# ssrv: Simple Serve(r\)

ssrv lets you quickly create custom endpoints using simple YAML configurations. No programming needed! 

While it was build with pentesting in mind, you can use for your own use cases.

What problem it solves for me:
- **Quick set up:** Spin up test endpoints in seconds.
- **Bug bounty hunting:** Craft specific responses for SSRF testing, etc.

## Features

- **Custom Response Headers:** Define headers like `Content-Type`, `Content-Length`, etc.
- **Any Content Length:** Manually control the `Content-Length` header to check for any weird behaviour.
- **Flexible Status Codes:** Choose any HTTP status code (e.g., 200, 403, 500, or even 1337 cause why not?!).
- **Custom Response Body:** Serve text directly, files, or even JSON responses.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/xplo1t-sec/ssrv
   cd ssrv
   ```

2. **Install Dependencies:**
   ```bash
   pip install Flask gunicorn
   ```

## Usage

1. **Create/Edit `config.yaml`:**
   - Define your desired endpoints (see the examples in `config.yaml`).
   - For file responses, make sure the files exist.

2. **Run the Server:**
   ```bash
   gunicorn -c gunicorn_config.py main:app
   ```
   This starts the server on `http://0.0.0.0:8000` using Gunicorn for better performance. Also, to remove certain headers, I used Gunicorn. I wasn't able to find any ways to do it from flask itself. I'm not a good programmer :3

## Configuration

### `config.yaml` Structure

Each entry in the YAML file represents one endpoint:

```
- path: /your/endpoint/path
  status_code: 200  # Optional (defaults to 200)
  headers: 
    Header-Name: Header-Value
    ... 
  body:
    type: text # or file (Required)
    content: "Your text content" # or path/to/file
```

### Gunicorn Configuration

The `gunicorn_config.py` file provides Gunicorn settings. Modify it for your production environment. You may add additional parameters which you can find on [Gunicorn docs](https://docs.gunicorn.org/en/latest/settings.html).

## Examples

See the included `config.yaml` for examples of various response types and status codes.

## Contributing

Feel free to submit issues or pull requests to improve ssrv!

## License

This project is licensed under the MIT License.
