import time
from machine import Pin, PWM, ADC

# Configuração do PWM (saída) e ADC (entrada)
pwm_out = PWM(Pin(16))  
pwm_out.freq(1000)  
adc_in = ADC(Pin(26)) 

# Configuração inicial de parâmetros para o lock-in
samples = 100 
amp = 2**15  
freq_ref_initial = 5.1  
intervalo_ref_initial = 1 / freq_ref_initial  
previous_input_value = 0  
signals = []  

# Função para implementar um filtro passa-baixa simples
def low_pass_filter(input_signal, previous_output, alpha=0.1):
    return alpha * input_signal + (1 - alpha) * previous_output


def read_adc():
    conversion_factor = 3.3 / 65535  
    return adc_in.read_u16() * conversion_factor 

# Função para calcular a média dos sinais armazenados
def calculate_average_signal(signals):
    return sum(signals) / len(signals)  

# Função para calcular o valor de lock-in
def lock_in_detection(input_signal, average_signal):
    """
    Realiza a multiplicação do sinal de entrada com o sinal médio.
    input_signal: sinal de entrada filtrado
    average_signal: média acumulada do sinal (referência)
    """
    return input_signal * average_signal  # Multiplica os dois sinais

lock_in_values = []

# Função principal que implementa o algoritmo de lock-in
def main_lock_in():
    global previous_input_value, signals

    # Leitura e pré-processamento do sinal de entrada
    x = 0.5 + 0.6 * read_adc()  # Escala e desloca o valor do ADC
    filtered_input = low_pass_filter(x, previous_input_value)  # Aplica o filtro passa-baixa
    signals = signals + [filtered_input]  # Adiciona o valor filtrado à lista de sinais

    # Garante que a lista de sinais não exceda o número de amostras
    if len(signals) > samples:
        signals.pop(0)  # Remove o valor mais antigo

    # Calcula o valor médio do sinal
    average_signal = calculate_average_signal(signals)

    # Calcula o valor de lock-in
    lock_in_value = lock_in_detection(filtered_input, average_signal)

    # Calcula o duty cycle para o PWM com base no valor de lock-in
    duty_cycle = round(amp * (1 + lock_in_value))  # Ajusta a escala para o PWM
    pwm_out.duty_u16(duty_cycle)  # Aplica o duty cycle no PWM

    # Exibe o valor de lock-in no console
    print(f"Valor Lock-in: {lock_in_value:.4f}")

    # Aguarda o próximo intervalo baseado na frequência de referência
    time.sleep(intervalo_ref_initial / samples)

    # Atualiza o valor filtrado anterior para a próxima iteração
    previous_input_value = filtered_input

    # Retorna o valor calculado de lock-in
    return lock_in_value







