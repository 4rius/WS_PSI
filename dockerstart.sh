#!/bin/sh
waitress-serve --call --port=$PORT "flaskr:create_app"
