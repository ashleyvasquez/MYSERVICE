import os
import json
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from openai import OpenAI

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar la API de OpenAI con la clave de entorno
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Inicializa la aplicación Flask
app = Flask(__name__)

# Cargar datos desde el archivo JSON
def load_data():
    with open('recommendations.json', 'r') as file:
        return json.load(file)

class RequestHandler:
    @staticmethod
    def validate_input(recommendation_type, value, connection_method):
        valid_types = ['genre', 'song', 'place']
        valid_methods = ['json', 'ai']

        if recommendation_type not in valid_types:
            return False, {"message": "Tipo de recomendación no válido. Debe ser 'genre', 'song' o 'place'."}, 400
        
        if not value or not isinstance(value, str):
            return False, {"message": "Valor de la recomendación no proporcionado o no válido."}, 400
        
        if connection_method not in valid_methods:
            return False, {"message": "Método de conexión no válido. Debe ser 'json' o 'ai'."}, 400

        return True, None, None

class RecommendationHandler:
    @staticmethod
    def process_request(recommendation_type, value, connection_method):
        if connection_method == 'json':
            return JSONRecommendation.get_recommendation(recommendation_type, value)
        elif connection_method == 'ai':
            return AIRecommendation.get_recommendation(value)

class JSONRecommendation:
    @staticmethod
    def get_recommendation(recommendation_type, value):
        data = load_data()
        
        if recommendation_type == 'place':
            recommendations = data['recommendations']['places']
        elif recommendation_type == 'genre':
            recommendations = data['recommendations']['genres']
        elif recommendation_type == 'song':
            recommendations = data['recommendations']['songs']
        
        if value in recommendations:
            return recommendations[value], 200
        else:
            return {"message": f"No se encontraron recomendaciones para '{recommendation_type}' con valor '{value}'."}, 404

class AIRecommendation:
    @staticmethod
    def get_recommendation(input_value):
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Te voy a dar una canción/género musical/lugar en el siguiente input {input_value}, dame como respuesta únicamente una recomendacion de los otros dos que no te di",
                    }
                ],
                model="gpt-3.5-turbo",
            )
            ai_recommendation = response.choices[0].message.content.strip()
            return {"recommendation": ai_recommendation}, 200
        except Exception as e:
            return {"message": f"Error al obtener la recomendación de AI: {str(e)}"}, 500

# Endpoint principal para manejar las solicitudes
@app.route('/recommendations', methods=['POST'])
def get_recommendation():
    """Obtener recomendación basada en tipo, valor y método de conexión"""
    body = request.json
    recommendation_type = body.get('type')
    value = body.get('value')
    connection_method = body.get('connection_method')
    
    valid, error_message, error_code = RequestHandler.validate_input(recommendation_type, value, connection_method)
    
    if not valid:
        return jsonify(error_message), error_code

    result, status_code = RecommendationHandler.process_request(recommendation_type, value, connection_method)
    
    if status_code == 404:
        return jsonify(result), status_code

    return jsonify(result), status_code

if __name__ == '__main__':
    app.run(debug=True)
