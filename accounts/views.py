from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
from .models import Pengguna, Member, Staf
from datetime import date


def landing_page(request):
    return render(request, 'base.html')


def login_view(request):
    if request.session.get('role'):
        if request.session.get('role') == 'member':
            return redirect('/member/dashboard/')
        elif request.session.get('role') == 'staf':
            return redirect('/staff/dashboard/')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Ambil data pengguna dari DB
        with connection.cursor() as cur:
            cur.execute("""
                SELECT email, password, salutation, first_mid_name, last_name,
                       country_code, mobile_number, tanggal_lahir, kewarganegaraan
                FROM pengguna
                WHERE email = %s
            """, [email])
            row = cur.fetchone()

        if not row:
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')
            return render(request, 'accounts/login.html')

        (db_email, db_password, salutation, first_mid_name, last_name,
         country_code, mobile_number, tanggal_lahir, kewarganegaraan) = row

        # Cek password (support hashed maupun plaintext sementara)
        password_valid = check_password(password, db_password)

        if not password_valid:
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')
            return render(request, 'accounts/login.html')

        def clean_val(val):
            if val is None or str(val).strip().lower() in ('none', ''):
                return ''
            return str(val).strip()

        request.session['email']          = db_email
        request.session['salutation']     = clean_val(salutation)
        request.session['first_mid_name'] = clean_val(first_mid_name)
        request.session['last_name']      = clean_val(last_name)
        request.session['nama']           = f"{request.session['first_mid_name']} {request.session['last_name']}".strip()
        request.session['country_code']   = clean_val(country_code)
        request.session['mobile_number']  = clean_val(mobile_number)
        request.session['tanggal_lahir']  = clean_val(tanggal_lahir)
        request.session['kewarganegaraan']= clean_val(kewarganegaraan)

        with connection.cursor() as cur:
            cur.execute("""
                SELECT m.nomor_member, m.tanggal_bergabung, m.id_tier,
                       m.award_miles, m.total_miles, t.nama
                FROM member m
                JOIN tier t ON t.id_tier = m.id_tier
                WHERE m.email = %s
            """, [email])
            member_row = cur.fetchone()

        if member_row:
            request.session['role']              = 'member'
            request.session['nomor_member']      = member_row[0]
            request.session['tanggal_bergabung'] = str(member_row[1])
            request.session['id_tier']           = member_row[2]
            request.session['award_miles']       = member_row[3]
            request.session['total_miles']       = member_row[4]
            request.session['tier']              = member_row[5]

            messages.success(request, f"Selamat datang, {salutation} {first_mid_name} {last_name}!")
            return redirect('/member/dashboard/')

        with connection.cursor() as cur:
            cur.execute("""
                SELECT s.id_staf, s.kode_maskapai, mk.nama_maskapai
                FROM staf s
                JOIN maskapai mk ON mk.kode_maskapai = s.kode_maskapai
                WHERE s.email = %s
            """, [email])
            staf_row = cur.fetchone()

        if staf_row:
            request.session['role']          = 'staf'
            request.session['id_staf']       = staf_row[0]
            request.session['kode_maskapai'] = staf_row[1]
            request.session['maskapai']      = staf_row[2]

            messages.success(request, f"Selamat datang, {salutation} {first_mid_name} {last_name}!")
            return redirect('/staff/dashboard/')

        # Email ada di pengguna tapi bukan member/staf
        messages.error(request, 'Akun tidak memiliki role yang valid.')

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.session.get('role'):
        return redirect('accounts:dashboard')

    MASKAPAI_CHOICES = [
        ('GA', 'GA - Garuda Indonesia'),
        ('QG', 'QG - Citilink'),
        ('JT', 'JT - Lion Air'),
        ('ID', 'ID - Batik Air'),
        ('SQ', 'SQ - Singapore Airlines'),
    ]

    if request.method == 'POST':
        role       = request.POST.get('role', 'member')
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')

        if not email:
            messages.error(request, 'Email tidak boleh kosong.')
            return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})

        # ambil data form
        hashed_password = make_password(password)
        salutation      = request.POST.get('salutation', '')
        # menggunakan nama_depan & nama_belakang sesuai dengan HTML form kamu
        first_mid_name  = request.POST.get('nama_depan', '')
        last_name       = request.POST.get('nama_belakang', '')
        country_code    = request.POST.get('country_code') or None
        mobile_number   = request.POST.get('mobile_number') or None
        tanggal_lahir   = request.POST.get('tanggal_lahir') or None
        kewarganegaraan = request.POST.get('kewarganegaraan') or None

        # insertion and auto increment
        # insertion and auto increment
        try:
            with connection.cursor() as cur:
                # insert ke pengguna 
                cur.execute("""
                    INSERT INTO pengguna (
                        email, password, salutation, first_mid_name, last_name,
                        country_code, mobile_number, tanggal_lahir, kewarganegaraan
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [email, hashed_password, salutation, first_mid_name, last_name,
                      country_code, mobile_number, tanggal_lahir, kewarganegaraan])

                # insert ke tabel spesifik berdasarkan rolenya
                if role == 'member':
                    cur.execute("""
                        SELECT MAX(CAST(SUBSTRING(nomor_member FROM 2) AS INTEGER)) 
                        FROM member
                    """)
                    max_id = cur.fetchone()[0]
                    next_number = 1 if max_id is None else max_id + 1
                    nomor_member = f"M{next_number:04d}"

                    cur.execute("""
                        INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                        VALUES (%s, %s, %s, 'T01', 0, 0)
                    """, [email, nomor_member, date.today()])

                elif role == 'staf':
                    kode_maskapai = request.POST.get('kode_maskapai', '')
                    
                    cur.execute("""
                        SELECT MAX(CAST(SUBSTRING(id_staf FROM 2) AS INTEGER)) 
                        FROM staf
                    """)
                    max_id = cur.fetchone()[0]
                    next_number = 1 if max_id is None else max_id + 1
                    id_staf = f"S{next_number:04d}"

                    cur.execute("""
                        INSERT INTO staf (email, id_staf, kode_maskapai)
                        VALUES (%s, %s, %s)
                    """, [email, id_staf, kode_maskapai])

            # Jika sukses tanpa terkena trigger
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('accounts:login')

        except Exception as e:
            # Tangkap lemparan error dari Trigger
            pesan_error = str(e).split('\n')[0].strip()
            
            if "ERROR: Email" in pesan_error:
                # Tampilkan pesan sama persis dengan yang dari database
                messages.error(request, pesan_error)
            else:
                messages.error(request, f"Terjadi kesalahan: {pesan_error}")
                
            return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})
        
    return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})

def logout_view(request):
    request.session.flush()
    messages.info(request, 'Anda telah logout.')
    return redirect('accounts:login')


def dashboard_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    if role == 'member':
        return redirect('/member/dashboard/')
    elif role == 'staf':
        return redirect('/staff/dashboard/')

    return redirect('accounts:login')


def profile_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    def clean_val(val):
        if val is None or str(val).strip().lower() in ('none', ''):
            return ''
        return str(val).strip()

    context = {
        'email'          : clean_val(request.session.get('email')),
        'role'           : role,
        'salutation'     : clean_val(request.session.get('salutation')),
        'first_mid_name' : clean_val(request.session.get('first_mid_name')),
        'last_name'      : clean_val(request.session.get('last_name')),
        'country_code'   : clean_val(request.session.get('country_code')),
        'mobile_number'  : clean_val(request.session.get('mobile_number')),
        'tanggal_lahir'  : clean_val(request.session.get('tanggal_lahir')),
        'kewarganegaraan': clean_val(request.session.get('kewarganegaraan')),
        'nomor_member'   : clean_val(request.session.get('nomor_member')),
        'tanggal_bergabung': clean_val(request.session.get('tanggal_bergabung')),
        'id_staf'        : clean_val(request.session.get('id_staf')),
        'kode_maskapai'  : clean_val(request.session.get('kode_maskapai')),
        'maskapai_choices': [
            ('GA', 'Garuda Indonesia'),
            ('QG', 'Citilink'),
            ('JT', 'Lion Air'),
            ('ID', 'Batik Air'),
            ('SQ', 'Singapore Airlines'),
        ],
    }

    if role == 'member':
        return render(request, 'profile_member.html', context)
    elif role == 'staf':
        return render(request, 'profile_staff.html', context)

    return redirect('accounts:dashboard')

def update_profile(request):
    if request.method == 'POST':
        email = request.session.get('email')
        salutation = request.POST.get('salutation', '').strip()
        first_mid_name = request.POST.get('first_mid_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        kewarganegaraan = request.POST.get('kewarganegaraan', '').strip()
        country_code = request.POST.get('country_code', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        tanggal_lahir = request.POST.get('tanggal_lahir', '').strip()

        if not all([salutation, first_mid_name, last_name, kewarganegaraan, country_code, mobile_number, tanggal_lahir]):
            messages.error(request, 'Gagal: Semua field profil wajib diisi!')
            return redirect('accounts:profile')

        try:
            with connection.cursor() as cur:
                cur.execute("""
                    UPDATE pengguna
                    SET salutation = %s, first_mid_name = %s, last_name = %s,
                        kewarganegaraan = %s, country_code = %s,
                        mobile_number = %s, tanggal_lahir = %s
                    WHERE email = %s
                """, [salutation, first_mid_name, last_name, kewarganegaraan, country_code, mobile_number, tanggal_lahir, email])
            
            request.session['salutation'] = salutation
            request.session['first_mid_name'] = first_mid_name
            request.session['last_name'] = last_name
            request.session['nama'] = f"{first_mid_name} {last_name}"
            request.session['kewarganegaraan'] = kewarganegaraan
            request.session['country_code'] = country_code
            request.session['mobile_number'] = mobile_number
            request.session['tanggal_lahir'] = str(tanggal_lahir)
            
            messages.success(request, 'Profil berhasil diperbarui.')
            
        except Exception as e:
            messages.error(request, f'Gagal memperbarui profil: {str(e)}')

        return redirect('accounts:profile')


def update_profile_photo(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    if request.method == 'POST':
        messages.info(request, 'Upload foto belum disambungkan ke database/media.')

    return redirect('accounts:profile')


def update_password(request):
    if not request.session.get('email'):
        return redirect('accounts:login')

    if request.method != 'POST':
        return redirect('accounts:profile')

    email               = request.session.get('email')
    password_lama       = request.POST.get('password_lama', '')
    password_baru       = request.POST.get('password_baru', '')
    konfirmasi_password = request.POST.get('konfirmasi_password_baru', '')

    with connection.cursor() as cur:
        cur.execute("SELECT password FROM pengguna WHERE email = %s", [email])
        row = cur.fetchone()

    if not row:
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('accounts:profile')

    if not check_password(password_lama, row[0]):
        messages.error(request, 'Password lama tidak sesuai.')
    elif password_baru != konfirmasi_password:
        messages.error(request, 'Konfirmasi password baru tidak cocok.')
    elif len(password_baru) < 8:
        messages.error(request, 'Password baru minimal 8 karakter.')
    else:
        hashed = make_password(password_baru)
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE pengguna SET password = %s WHERE email = %s",
                [hashed, email]
            )
        messages.success(request, 'Password berhasil diubah.')

    return redirect('accounts:profile')