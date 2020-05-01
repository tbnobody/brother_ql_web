## brother\_ql\_web

This is a web service to print labels on Brother QL label printers.

You need Python 3 for this software to work.

![Screenshot](./screenshots/Label-Designer_Desktop.png)

The web interface is [responsive](https://en.wikipedia.org/wiki/Responsive_web_design).
There's also a screenshot showing [how it looks on a smartphone](./screenshots/Label-Designer_Phone.png)

### Additional Features
* Print text as QR Code
    * Add text to QR Code
    * Change size of QR Code
* Upload files to print
    * .pdf, .png and .jpg files
    * automatically convertion to black/white image
* Change print color for black/white/red labels
* Print lables multiple times
    * Cut every label
    * Cut only after the last label
* Migrated GUI to Bootstrap 4
* Make preview for round labels.. round

### Installation

This installation manual requires only a default installation of Debian 10 (Buster).
Install prerequisites:

    apt install fontconfig python3-venv python3-pip git poppler-utils

Get the code:

    cd /opt
    git clone https://github.com/tbnobody/brother_ql_web.git

Build the venv and install the requirements:

    cd /opt/brother_ql_web
    python3 -m venv .venv
    source /opt/brother_ql_web/.venv/bin/activate
    pip install -r requirements.txt

### Configuration file

Copy `config.example.json` to `config.json` (e.g. `cp config.example.json config.json`) and adjust the values to match your needs.

### Startup

To start the server, run `./run.py`.

### Automatic startup using systemd service

Copy service file, reload system, enable and start the service

    cp /opt/brother_ql_web/systemd/brother_ql_web.service /etc/systemd/system
    systemctl daemon-reload
    systemctl enable brother_ql_web
    systemctl start brother_ql_web

### Usage

Once it's running, access the web interface by opening the page with your browser.
If you run it on your local machine, go to <http://localhost:8013> (You can change
the default port 8013 using the --port argument).
You will then be forwarded by default to the interactive web gui located at `/labeldesigner`.

All in all, the web server offers:

* a Web GUI allowing you to print your labels at `/labeldesigner`,
* an API at `/api/print/text?text=Your_Text&font_size=100&font_family=Minion%20Pro%20(%20Semibold%20)`
  to print a label containing 'Your Text' with the specified font properties.

### License

This software is published under the terms of the GPLv3, see the LICENSE file in the repository.

Parts of this package are redistributed software products from 3rd parties. They are subject to different licenses:

* [Bootstrap](https://github.com/twbs/bootstrap), MIT License
* [Font Awesome](https://github.com/FortAwesome/Font-Awesome), CC BY 4.0 License
* [jQuery](https://github.com/jquery/jquery), MIT License
