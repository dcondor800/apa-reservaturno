from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from flask_mail import Mail, Message
from email.mime.image import MIMEImage
import csv
import os
from datetime import datetime
from functools import wraps

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'avem2025'

app = Flask(__name__)

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'avem.inscripciones@apa.org.pe'
app.config['MAIL_PASSWORD'] = 'kofr rgyf qbev rfvv'
app.config['MAIL_DEFAULT_SENDER'] = 'avem.inscripciones@apa.org.pe'
mail = Mail(app)

CSV_FILE = 'turnos.csv'

# --- Asegura que exista el archivo CSV con encabezados ---
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])

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

# --- Ruta protegida para descargar el CSV ---
@app.route('/descargar-turnos')
@autenticar
def descargar_turnos():
    if os.path.exists(CSV_FILE):
        return send_file(
            CSV_FILE,
            as_attachment=True,
            download_name='turnos_avem.csv'
        )
    else:
        return "Archivo de turnos no encontrado", 404

# --- Ruta protegida para reiniciar turnos ---
@app.route('/reiniciar-turnos')
@autenticar
def reiniciar_turnos():
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])
        return "Archivo de turnos reiniciado correctamente."
    except Exception as e:
        return f"Error al reiniciar el archivo: {e}", 500

# --- Página principal ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Generar turno ---
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
    numero_existente = None
    nombre_existente = None

    # Verificar si archivo está vacío
    if not os.path.isfile(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Turno', 'Nombre', 'Empresa', 'Email', 'Celular', 'País', 'Hora'])

    # Leer turnos
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        try:
            encabezado = next(reader)
        except StopIteration:
            encabezado = []
        for row in reader:
            if row:
                if row[3].strip().lower() == email.strip().lower():
                    cliente_ya_registrado = True
                    numero_existente = row[0]
                    nombre_existente = row[1]
                    break
                if row[0].isdigit():
                    ultimo_turno = max(ultimo_turno, int(row[0]))

    if cliente_ya_registrado:
        return render_template('confirmacion.html', turno=numero_existente, nombre=nombre_existente)

    nuevo_turno = ultimo_turno + 1

    # Guardar nuevo turno
    with open(CSV_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([nuevo_turno, nombre, empresa, email, celular, pais, hora])

    # Enviar email de confirmación
    try:
        msg = Message(
            subject=f"🎫 Registro AVEM 2025 – Turno Nº{nuevo_turno}",
            sender=("RESERVAS APA", app.config['MAIL_USERNAME']),
            recipients=[email]
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; font-size: 15px; color: #333;">
            <p>¡Gracias por tu interés en formar parte del <strong>Congreso de Avicultura AVEM 2025</strong>!</p>

            <p>Hemos recibido tu registro exitosamente y este es tu número de atención:</p>

            <h2 style="font-size: 28px; color: #005baa; margin: 15px 0;">Nº{nuevo_turno}</h2>

            <p>Con este número podrás ser atendido el día de nuestro aniversario, <strong>jueves 26 de junio</strong>, en nuestro módulo.</p>

            <h3 style="margin-top: 25px;">¿Cómo funciona?</h3>

            <ol>
                <li><strong>Proyección del número:</strong> El día del evento, proyectaremos tu número en una pantalla. Tendrás <strong>2 minutos</strong> para acercarte al módulo antes de llamar al siguiente número.</li>
                <li><strong>Selección del stand:</strong> Podrás escoger tu espacio en AVEM 2025, de acuerdo al plano proyectado.</li>
                <li><strong>Confirmación inmediata:</strong> Recibirás un correo con la confirmación formal de tu reserva.</li>
                <li><strong>Proceso de compra:</strong> A partir del lunes 30 de junio, nos comunicaremos contigo para enviarte el contrato y finalizar tu participación.</li>
            </ol>

            <p style="color: #a00;"><strong>Importante:</strong> Este registro no asegura tu espacio en el AVEM 2025 hasta que completes el proceso de atención presencial durante el evento.</p>

            <p style="margin-top: 20px;">¡Te esperamos puntualmente para vivir juntos el lanzamiento del AVEM 2025!</p>

            <p style="margin-top: 30px;">Atentamente,<br><strong>ASOCIACIÓN PERUANA DE AVICULTURA</strong></p>

            <br>
            <img src="cid:footer_img" style="max-width: 600px; width: 100%; margin-top: 30px;" alt="Footer AVEM" />
        </body>
        </html>
        """

        # Embebido de imagen al final (footer)
        ruta_footer = os.path.join(app.root_path, 'static', 'footer-apa.png')
        if os.path.exists(ruta_footer):
            with open(ruta_footer, 'rb') as f:
                img_data = f.read()
                img = MIMEImage(img_data, _subtype='png')
                img.add_header('Content-ID', '<footer_img>')
                img.add_header('Content-Disposition', 'inline', filename='footer-apa.png')
                msg.attach(
                    filename='footer-apa.png',
                    content_type='image/png',
                    data=img_data,
                    disposition='inline',
                    headers={'Content-ID': '<footer_img>'}
                )

        mail.send(msg)

    except Exception as e:
        print("Error al enviar correo:", e)

    return render_template('confirmacion.html', turno=nuevo_turno, nombre=nombre)

# --- Solo para entorno local ---
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

