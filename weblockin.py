import time
import network
import socket
from lockin import main_lock_in

# Configuração Wi-Fi
ssid = 'eel7121'
password = 'ufsc2023'

def connect():
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid=ssid, password=password)
    wlan.active(True)

    while not wlan.active():
        print("Aguardando conexão...")
        time.sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"Conectado em {ip}")
    return ip

# Servidor para exibir o gráfico
import time
import json

def serve(connection):
    lock_in_values = []
    time_values = []
    start_time = time.time()

    while True:
        client = connection.accept()[0]
        request = client.recv(1024).decode()

        if "/lockin" in request:
            current_time = time.time() - start_time
            lock_in_value = main_lock_in()  # Chama a função principal do arquivo `main`
            
            # Concatenando as novas listas aos dados antigos
            lock_in_values = lock_in_values + [lock_in_value]  # Concatena os novos valores à lista existente
            time_values = time_values + [current_time]  # Adiciona o current_time como uma nova lista

            # Mantém os dados para 100 amostras no gráfico
            if len(lock_in_values) > 100:
                lock_in_values = lock_in_values[1:]  # Remove o primeiro item (o mais antigo)
                time_values = time_values[1:]  # Remove o primeiro item de tempo

            # Prepara a resposta JSON
            response = {
                "time": time_values,
                "values": lock_in_values
            }

            # Envia a resposta HTTP com JSON
            client.send("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            client.send(json.dumps(response))  # Converte o dicionário para JSON
            client.close()
        else:
            html = web_page()  # Função que gera a página HTML
            client.send("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
            client.send(html)
            client.close()


# Página HTML com gráfico
def web_page():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h2>Lock-In Detection - Real-Time Plot</h2>
        <canvas id="chart" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('chart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Lock-In Value',
                        data: [],
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        x: { title: { display: true, text: 'Time (s)' } },
                        y: { title: { display: true, text: 'Lock-In Value' } }
                    }
                }
            });

            function updateChart() {
                fetch('/lockin')
                    .then(response => response.json())
                    .then(data => {
                        chart.data.labels = data.time.map(t => t.toFixed(2));
                        chart.data.datasets[0].data = data.values.map(v => v.toFixed(4));
                        chart.update();
                    });
            }

            setInterval(updateChart, 500);
        </script>
    </body>
    </html>
    """
    return html

def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(2)
    return connection

# Inicializa o servidor
try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    print("Servidor encerrado.")
