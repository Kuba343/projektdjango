from django.db import connection

def zadanie_zwolnij_rezerwacje():
    """Funkcja wywołująca procedurę SQL czyszczącą blokady"""
    with connection.cursor() as cursor:
        cursor.execute("CALL zwolnij_dlugo_oczekujace_rezerwacje()")
    print("LOG: Procedura SQL zwolnij_dlugo_oczekujace_rezerwacje została wykonana.")