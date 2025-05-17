from app import app # Importa a instância 'app' do nosso pacote 'app'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)