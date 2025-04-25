import io
import zipfile
import pandas as pd

# ... existing code ...

# Em vez de:
csv_data = df.to_csv(index=False)
zf.writestr(nome_arquivo, csv_data)

# Mudaria para:
excel_buffer = io.BytesIO()
df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)
zf.writestr(nome_arquivo.replace('.csv', '.xlsx'), excel_buffer.getvalue())

# ... existing code ...