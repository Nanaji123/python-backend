def verification_email_template(name, link):

    return f"""
    <html>
      <body style="background:#f4f4f4;padding:30px;font-family:Arial;">
        <div style="background:#fff;padding:30px;border-radius:10px;width:500px;margin:auto;">
          <h2>Verify your email</h2>

          <p>Hi <strong>{name}</strong>,</p>

          <p>
          Thanks for signing up! Click the button below to verify your email.
          </p>

          <div style="margin:25px 0;">
            <a href="{link}" 
               style="background:#4f46e5;color:white;padding:12px 25px;border-radius:6px;text-decoration:none;">
               Verify Email
            </a>
          </div>

          <p>This link will expire in <strong>1 hour</strong>.</p>
        </div>
      </body>
    </html>
    """

def password_reset_email_template(name, link):

    return f"""
    <html>
      <body style="background:#f4f4f4;padding:30px;font-family:Arial;">
        <div style="background:#fff;padding:30px;border-radius:10px;width:500px;margin:auto;">
          <h2>Reset your password</h2>

          <p>Hi <strong>{name}</strong>,</p>

          <p>
          Click the button below to reset your password.
          </p>

          <div style="margin:25px 0;">
            <a href="{link}" 
               style="background:#4f46e5;color:white;padding:12px 25px;border-radius:6px;text-decoration:none;">
               Reset Password
            </a>
          </div>

          <p>This link will expire in <strong>15 minutes</strong>.</p>
        </div>
      </body>
    </html>
    """