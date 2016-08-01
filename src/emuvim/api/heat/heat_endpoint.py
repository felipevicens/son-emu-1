import json
from flask import Flask, request, jsonify, abort

app = Flask(__name__)


@app.route('/', methods=['POST'])
# REST API listening on port 5000 for HEAT template

def heatAPIEndpoint():
    # Extracting the HEAT template from the request
    file_data = request.data
    # Calling heatAdapter function
    heatAdapter(file_data)
    # Return Success to the calling function
    return jsonify(file_data), 200
#HEAT Adapter which receives the HEAT template as parameter and instantiates VNF's on POP
def heatAdapter(file_data):
     print file_data
     return jsonify(file_data), 200


if __name__ == '__main__':
    app.run(debug=True)
