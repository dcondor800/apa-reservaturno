from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from flask_mail import Mail, Message
import csv
import os
from datetime import datetime
from functools import wraps

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'avem2025'

app = Flask(__name__)

# Define un decorador para proteger rutas

def autenticar(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return Response(
                'Acceso restringido.\nDebes iniciar sesión.', 401,
                {'WWW-Authenticate': 'Basic realm="Zona Administrativa"'}
            )
        return f(*args, **kwargs)
    return decorada

#Aplica el decorador a la ruta de descarga

@app.route('/descargar-turnos')
@autenticar
def descargar_turnos():
    if os.path.exists(CSV_FILE):
        return send_file(
            CSV_FILE,
            as_attachment=True,
            download_name='turnos_avem.csv'  # ← Nombre personalizado para la descarga
        )
    else:
        return "Archivo de turnos no encontrado", 404




# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dcondor79@gmail.com'
app.config['MAIL_PASSWORD'] = 'jiab sppf msnh bfqm'
app.config['MAIL_DEFAULT_SENDER'] = 'reservas-apa@gmail.com'

mail = Mail(app)

CSV_FILE = 'turnos.csv'

# --- Asegura que exista el archivo CSV con encabezados ---
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar-turno', methods=['POST'])
def generar_turno():
    nombre = request.form['nombre']
    empresa = request.form['empresa']
    email = request.form['email']
    celular = request.form['celular']
    pais = request.form['pais']
    hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    ultimo_turno = 0
    cliente_ya_registrado = False

    # Verificar existencia y contenido del CSV
    if not os.path.isfile(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        # Crear CSV con encabezados
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])

    # Leer turnos existentes para validar duplicados y calcular el último turno
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            encabezado = next(reader)  # Saltar encabezado
        except StopIteration:
            encabezado = []
        for row in reader:
            if row:
                if row[3].strip().lower() == email.strip().lower():
                    cliente_ya_registrado = True
                    numero_existente = row[0]
                    break
                if row[0].isdigit():
                    ultimo_turno = max(ultimo_turno, int(row[0]))

    if cliente_ya_registrado:
        return render_template('confirmacion.html', turno=numero_existente, empresa=empresa)


    nuevo_turno = ultimo_turno + 1

    # Guardar nuevo registro
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([nuevo_turno, nombre, empresa, email, celular, pais, hora])

    # Enviar email de confirmación
    try:
        msg = Message(f"Turno asignado para AVEM 2025: #{nuevo_turno}", recipients=[email])
        msg.body = (
            f"Estimado equipo de {empresa},\n\n"
            f"Gracias por registrarse para participar en la feria AVEM 2025.\n"
            f"Su número de turno asignado es: #{nuevo_turno}\n\n"
            f"Resumen de datos ingresados:\n"
            f"- Empresa: {empresa}\n"
            f"- Email de contacto: {email}\n"
            f"- Celular: {celular}\n"
            f"- País: {pais}\n"
            f"- Fecha de registro: {hora}\n\n"
            f"Conserven este número, ya que será requerido para seleccionar su stand.\n"
            f"¡Nos vemos en AVEM 2025!\n"
        )
        mail.send(msg)
    except Exception as e:
        print("Error al enviar correo:", e)


    return render_template('confirmacion.html', turno=nuevo_turno, empresa=empresa)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
