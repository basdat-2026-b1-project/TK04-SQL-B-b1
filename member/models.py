from django.db import models
from accounts.models import Pengguna, Member, Staf # Import dari app accounts

class Bandara(models.Model):
    iata_code = models.CharField(max_length=3, primary_key=True)
    nama = models.CharField(max_length=100)
    kota = models.CharField(max_length=100)
    negara = models.CharField(max_length=100)

    class Meta:
        db_table = 'BANDARA'
        managed = False

class Maskapai(models.Model):
    kode_maskapai = models.CharField(max_length=10, primary_key=True)
    nama_maskapai = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'MASKAPAI'
        managed = False

class ClaimMissingMiles(models.Model):
    id = models.AutoField(primary_key=True)
    email_member = models.ForeignKey(Member, on_delete=models.CASCADE, db_column='email_member')
    email_staf = models.ForeignKey(Staf, on_delete=models.SET_NULL, null=True, blank=True, db_column='email_staf')
    maskapai = models.ForeignKey(Maskapai, on_delete=models.CASCADE, db_column='maskapai')
    bandara_asal = models.ForeignKey(Bandara, on_delete=models.CASCADE, related_name='asal', db_column='bandara_asal')
    bandara_tujuan = models.ForeignKey(Bandara, on_delete=models.CASCADE, related_name='tujuan', db_column='bandara_tujuan')
    tanggal_penerbangan = models.DateField()
    flight_number = models.CharField(max_length=10)
    nomor_tiket = models.CharField(max_length=20)
    kelas_kabin = models.CharField(max_length=20)
    pnr = models.CharField(max_length=10)
    status_penerimaan = models.CharField(max_length=20, default='Menunggu')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'CLAIM_MISSING_MILES'
        managed = False
        unique_together = ('email_member', 'flight_number', 'tanggal_penerbangan', 'nomor_tiket')

class Transfer(models.Model):
    email_member_1 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='transfer_keluar', db_column='email_member_1')
    email_member_2 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='transfer_masuk', db_column='email_member_2')
    timestamp = models.DateTimeField(auto_now_add=True)
    jumlah = models.IntegerField()
    catatan = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'TRANSFER'
        managed = False
        unique_together = (('email_member_1', 'email_member_2', 'timestamp'),)