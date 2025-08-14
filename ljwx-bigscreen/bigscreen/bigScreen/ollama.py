from flask import jsonify, Response
import requests

def chat_with_ollama(prompt, model="deepseek-r1:70b"):
    """
    Send a chat request to Ollama server and get the response
    """
    url = "http://192.168.1.83:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        print(response.json())
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "error": f"Failed to get response from Ollama server. Status code: {response.status_code}"
            }), 500
    except Exception as e:
        return jsonify({
            "error": f"Error connecting to Ollama server: {str(e)}"
        }), 500

def chat_with_ollama_stream(prompt, model="deepseek-r1:70b"):
    """
    Send a chat request to Ollama server and stream the response
    """
    url = "http://192.168.1.83:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    try:
        response = requests.post(url, json=payload, stream=True)
        return Response(response.iter_lines(), 
                       content_type='application/json')
    except Exception as e:
        return jsonify({
            "error": f"Error connecting to Ollama server: {str(e)}"
        }), 500