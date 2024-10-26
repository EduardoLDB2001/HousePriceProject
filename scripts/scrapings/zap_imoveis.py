# Libs
import pandas as pd
import requests
import time
import os
import re
from bs4 import BeautifulSoup

# Constants
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track Request Header
    'TE': 'Trailers'
}


BASE_URL = 'https://www.zapimoveis.com.br/venda/apartamentos/df+brasilia/?transacao=venda&onde=,Distrito%20Federal,Bras%C3%ADlia,,,,,city,BR%3EDistrito%20Federal%3ENULL%3EBrasilia,-15.826691,-47.92182,&tipos=apartamento_residencial,studio_residencial,kitnet_residencial,casa_residencial,sobrado_residencial,condominio_residencial,casa-vila_residencial,cobertura_residencial,flat_residencial,loft_residencial&itl_id=1000072&itl_name=zap_-_botao-cta_buscar_to_zap_resultado-pesquisa?pagina=' # URL base do site com o parâmetro pagina para acessar diferentes páginas de listagem de imóveis.

NUM_PAGES = 5

REQUEST_DELAY = 10

# Function for extracting data from a single property
def extract_property_data(property_soup):
    def get_text_or_none(element, selector):
        selected_element = element.select_one(selector)
        return selected_element.get_text(strip=True) if selected_element else None

    # Descrição do imóvel
    description_element = property_soup.find('p', class_='ListingCard_card__description__slBTG')
    description = description_element['title'] if description_element else None

    # Preço total do imóvel
    price_element = property_soup.find('p', class_='l-text l-u-color-neutral-28 l-text--variant-heading-small l-text--weight-bold undefined')
    price = price_element.get_text(strip=True) if price_element else None

    # Tamanho em m²
    size_m2_element = property_soup.find('p', class_='l-text l-u-color-neutral-28 l-text--variant-body-small l-text--weight-regular undefined', itemprop='floorSize')
    size_m2 = size_m2_element.get_text(strip=True) if size_m2_element else None

    # Nº de quartos
    bedroom_element = property_soup.find('p', class_='l-text l-u-color-neutral-28 l-text--variant-body-small l-text--weight-regular undefined', itemprop='numberOfRooms')
    bedroom = bedroom_element.get_text(strip=True) if bedroom_element else None

    # Número de Vagas para carros
    car_spaces_element = property_soup.find('p', {'itemprop': 'numberOfParkingSpaces'})
    car_spaces = car_spaces_element.get_text(strip=True) if car_spaces_element else None

    # Bairro
    neighborhood_element = property_soup.find('h2', {'class': 'l-text', 'data-cy': 'rp-cardProperty-location-txt'})
    neighborhood = neighborhood_element['title'] if neighborhood_element else None

    # Endereço
    location_element = property_soup.find('p', {'class': 'l-text', 'data-cy': 'rp-cardProperty-street-txt'})
    location = location_element['title'] if location_element else None

    # Nº de banheiros
    bathrooms_element = property_soup.find('p', {'itemprop': 'numberOfBathroomsTotal'})
    bathrooms = bathrooms_element.get_text(strip=True) if bathrooms_element else None

    # Valores de condomínio e IPTU
    cond_iptu = get_text_or_none(property_soup, 'p.text-balance')

    # Status
    status = property_soup.find('div', class_='l-tag-card__content').get_text(strip=True) if property_soup.find('div', class_='l-tag-card__content') else None

    return {
        'description': description,
        'price': price,
        'size': size_m2,
        'bedrooms': bedroom,
        'car_spaces': car_spaces,
        'neighborhood': neighborhood,
        'location': location,
        'bathrooms': bathrooms,
        'cond_iptu': cond_iptu,
        'status': status
    }


# Function for scraping a single page \*

def scrape_page(page_number):
    url = f"{BASE_URL}{page_number}"
    response = requests.get(url, headers = HEADERS)

    if response.status_code != 200:
        print(f"Erro ao acessar a página {page_number}. Status code: {response.status_code}")
        return []

    site = BeautifulSoup(response.text, "html.parser")
    current_page = site.find('span', class_='active')

    if current_page:
        print(f"Raspando dados da página {current_page.get_text(strip=True)}...")

    properties = site.find_all('div', class_='ListingCard_result-card__Pumtx')
    return [extract_property_data(property_soup) for property_soup in properties]


# Function to scrape multiple pages

def scrape_multiple_pages(num_pages):
    all_properties = []

    for page in range(1, num_pages + 1):
        print(f"Raspando a página {page}...")
        try:
            properties = scrape_page(page)
            all_properties.extend(properties)
        except Exception as e:
            print(f"Erro ao raspar a página {page}: {e}")

        time.sleep(REQUEST_DELAY)

    return all_properties


# Function to save data to a DataFrame

def create_dataframe(properties_data):
    if not properties_data:
        print("Nenhuma propriedade foi encontrada.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se a lista estiver vazia

    # Cria um DataFrame com a lista de dicionários
    df = pd.DataFrame(properties_data)

    print(f"DataFrame criado com {len(df)} registros.")
    return df

# Save xlsx

def save_to_excel(df, filename):
    if df.empty:
        print("O DataFrame está vazio. Nenhum arquivo Excel foi salvo.")
        return

    try:
        # Salvando o DataFrame no arquivo Excel
        df.to_excel(filename, index=False)
        print(f"Arquivo Excel salvo como {filename}")
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo Excel: {e}")


# Main script \*

if __name__ == "__main__":
    try:
        # Raspando dados de múltiplas páginas
        properties_data = scrape_multiple_pages(NUM_PAGES)

        # Verificando se há dados para criar o DataFrame
        if properties_data:
            df = create_dataframe(properties_data)

            # Exibindo o DataFrame e o diretório de trabalho atual
            print(df.head())  # Mostra apenas as primeiras linhas do DataFrame
            print(f"Diretório atual de trabalho: {os.getcwd()}")

            # Salvando o DataFrame em um arquivo Excel
            save_to_excel(df, 'imoveis_df.xlsx')
        else:
            print("Nenhum dado foi raspado. O DataFrame não será criado.")
    except Exception as e:
        print(f"Ocorreu um erro no script principal: {e}")
