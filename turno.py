
from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from flask_mail import Mail, Message
from email.mime.image import MIMEImage
import csv
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# --- Configuración de seguridad ---
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'avem2025'

# --- Archivo de datos ---
CSV_FILE = 'turnos.csv'

# --- Decorador para autenticación básica ---
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

# --- Configuración de correo ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'avem.inscripciones@apa.org.pe'
app.config['MAIL_PASSWORD'] = 'kofr rgyf qbev rfvv'
app.config['MAIL_DEFAULT_SENDER'] = ('RESERVAS APA', 'avem.inscripciones@apa.org.pe')
mail = Mail(app)

# --- Asegura que exista el CSV con encabezados ---
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])

# --- Rutas de la aplicación ---
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

    # Leer CSV para buscar duplicado
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            encabezado = next(reader)
        except StopIteration:
            encabezado = []

        for row in reader:
            if row and row[3].strip().lower() == email.strip().lower():
                cliente_ya_registrado = True
                numero_existente = row[0]
                nombre_existente = row[1]
                break
            if row and row[0].isdigit():
                ultimo_turno = max(ultimo_turno, int(row[0]))

    if cliente_ya_registrado:
        return render_template('confirmacion.html', turno=numero_existente, nombre=nombre_existente)

    nuevo_turno = ultimo_turno + 1

    # Guardar nuevo registro
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([nuevo_turno, nombre, empresa, email, celular, pais, hora])

    # Enviar correo de confirmación
    try:
        msg = Message(
            subject=f"Turno asignado para AVEM 2025: #{nuevo_turno}",
            recipients=[email]
        )
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; font-size: 15px; color: #333;">
            <p>Estimado equipo de <strong>{empresa}</strong>,</p>
            <p>Gracias por registrarse para participar en la feria <strong>AVEM 2025</strong>.</p>
            <p><strong>Su número de turno asignado es: #{nuevo_turno}</strong></p>
            <p>Resumen de datos ingresados:</p>
            <ul>
                <li>📌 <strong>Empresa:</strong> {empresa}</li>
                <li>📧 <strong>Email:</strong> {email}</li>
                <li>📱 <strong>Celular:</strong> {celular}</li>
                <li>🌎 <strong>País:</strong> {pais}</li>
                <li>📅 <strong>Fecha:</strong> {hora}</li>
            </ul>
            <p>Conserven este número, ya que será requerido para seleccionar su stand.</p>
            <p>¡Nos vemos en AVEM 2025!</p>
            <br>
            <img src="cid:footer_img" style="max-width: 600px; width: 100%; margin-top: 20px;" alt="Footer AVEM">
        </body>
        </html>
        """
        # Imagen embebida
        ruta_footer = os.path.join(app.root_path, 'static', 'footer-apa.png')
        if os.path.exists(ruta_footer):
            with open(ruta_footer, 'rb') as f:
                img_data = f.read()
                img = MIMEImage(img_data, _subtype='png')
                img.add_header('Content-ID', '<footer_img>')
                img.add_header('Content-Disposition', 'inline', filename='footer-apa.png')
                msg.attach(filename='footer-apa.png', content_type='image/png', data=img_data,
                           disposition='inline', headers={'Content-ID': '<footer_img>'})
        mail.send(msg)
    except Exception as e:
        print("Error al enviar correo:", e)

    return render_template('confirmacion.html', turno=nuevo_turno, nombre=nombre)


# --- Ruta para descargar CSV protegida ---
@app.route('/descargar-turnos')
@autenticar
def descargar_turnos():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True, download_name='turnos_avem.csv')
    return "Archivo no encontrado", 404


# --- Ruta para reiniciar el CSV con encabezado ---
@app.route('/reiniciar-turnos')
@autenticar
def reiniciar_turnos():
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])
        return "turnos.csv ha sido reiniciado correctamente."
    except Exception as e:
        return f"Error al reiniciar archivo: {e}", 500


if __name__ == '__main__':
    app.run()

