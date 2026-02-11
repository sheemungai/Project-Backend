import pandas as pd
from django.core.management.base import BaseCommand
from careers.models import Institution, Course
from django.db import transaction


class Command(BaseCommand):
    help = 'Import KUCCPS data from Excel file'

    def handle(self, *args, **kwargs):
        file_path = 'kuccps_data.xlsx.xlsx'
        
        self.stdout.write(self.style.WARNING(f'Starting import from {file_path}...'))
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(df)} rows to import'))
            
            imported_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Get institution name
                        institution_name = str(row['INSTITUTION NAME']).strip()
                        
                        # Skip if institution name is empty or NaN
                        if pd.isna(institution_name) or institution_name == '' or institution_name == 'nan':
                            skipped_count += 1
                            continue
                        
                        # Get or create institution
                        institution, created = Institution.objects.get_or_create(
                            name=institution_name,
                            defaults={'location': ''}  # You can update this manually later
                        )
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created institution: {institution_name}'))
                        
                        # Get program details
                        prog_code = str(row['PROG CODE']).strip()
                        programme_name = str(row['PROGRAMME NAME']).strip()
                        
                        # Skip if essential fields are empty
                        if pd.isna(prog_code) or pd.isna(programme_name) or prog_code == 'nan':
                            skipped_count += 1
                            continue
                        
                        # Helper function to safely convert cutoff values
                        def safe_decimal(value):
                            if pd.isna(value) or value == '' or value == '-':
                                return None
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                return None
                        
                        # Create or update course
                        course, created = Course.objects.update_or_create(
                            prog_code=prog_code,
                            defaults={
                                'name': programme_name,
                                'institution': institution,
                                'cutoff_2018': safe_decimal(row.get('2018 CUTOFF')),
                                'cutoff_2019': safe_decimal(row.get('2019 CUTOFF')),
                                'cutoff_2020': safe_decimal(row.get('2020 CUTOFF')),
                                'cutoff_2021': safe_decimal(row.get('2021 CUTOFF')),
                                'cutoff_2022': safe_decimal(row.get('2022 CUTOFF')),
                                'cutoff_2023': safe_decimal(row.get('2023 CUTOFF')),
                                'cutoff_2024': safe_decimal(row.get('2024 CUTOFF')),
                                'cutoff_2025': safe_decimal(row.get('2025 CUTOFF')),
                            }
                        )
                        
                        imported_count += 1
                        
                        if created:
                            self.stdout.write(f'✓ Imported: {prog_code} - {programme_name}')
                        else:
                            self.stdout.write(f'↻ Updated: {prog_code} - {programme_name}')
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error at row {index}: {str(e)}'))
                        skipped_count += 1
                        continue
            
            self.stdout.write(self.style.SUCCESS(f'\n=== Import Complete ==='))
            self.stdout.write(self.style.SUCCESS(f'Successfully imported: {imported_count} courses'))
            self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count} rows'))
            self.stdout.write(self.style.SUCCESS(f'Total institutions: {Institution.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'Total courses: {Course.objects.count()}'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            self.stdout.write(self.style.ERROR('Make sure the file is in the project root directory'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))