from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('strona', '0006_rental_created_at_alter_car_year'), # Tu Django samo wpisało poprzednika, zostaw to!
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- 1. ZNIŻKA LOJALNOŚCIOWA
            CREATE OR REPLACE FUNCTION znizka_lojalnosciowa(f_user_id INT)
            RETURNS INT AS $$DECLARE
                v_liczba_wypozyczen INT;
                v_rabat INT;
            BEGIN
                SELECT COUNT(*) INTO v_liczba_wypozyczen FROM strona_rental WHERE user_id = f_user_id;
                IF v_liczba_wypozyczen >= 20 THEN v_rabat := 20;
                ELSIF v_liczba_wypozyczen >= 10 THEN v_rabat := 10;
                ELSE v_rabat := 0;
                END IF;
                RETURN v_rabat;
            END;$$ LANGUAGE plpgsql;

            -- 2. OBLICZANIE CENY
            CREATE OR REPLACE FUNCTION oblicz_cene_wypozyczenia(f_id_car INT, f_id_addon INT, f_days INT, f_user_id INT)
            RETURNS DECIMAL AS $$DECLARE
                v_cena_auta DECIMAL;
                v_cena_dodatku DECIMAL;
                v_wynik DECIMAL;
                v_rabat INT;
            BEGIN
                SELECT (price_per_day * f_days) INTO v_cena_auta FROM strona_car WHERE id = f_id_car;
                SELECT COALESCE(daily_price * f_days, 0) INTO v_cena_dodatku FROM strona_addon WHERE id = f_id_addon;
                v_wynik := v_cena_auta + v_cena_dodatku;
                v_rabat := COALESCE(znizka_lojalnosciowa(f_user_id), 0);
                RETURN v_wynik * ((100.0 - v_rabat) / 100.0);
            END;$$ LANGUAGE plpgsql;

            -- 3. ILOŚĆ AUT W ODDZIALE
            CREATE OR REPLACE FUNCTION oblicz_ilosc_aut_w_oddziale(f_id_oddzialu INT)
            RETURNS INT AS $$BEGIN
                RETURN (SELECT COUNT(*) FROM strona_car WHERE current_branch_id = f_id_oddzialu);
            END;$$ LANGUAGE plpgsql;
            """,
            reverse_sql="""
            DROP FUNCTION IF EXISTS oblicz_ilosc_aut_w_oddziale(INT);
            DROP FUNCTION IF EXISTS oblicz_cene_wypozyczenia(INT, INT, INT, INT);
            DROP FUNCTION IF EXISTS znizka_lojalnosciowa(INT);
            """
        ),
    ]