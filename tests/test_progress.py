def test_list_modules_endpoint(client):
    """
    Valida el contrato del endpoint GET /api/modules:
    - Retorna código HTTP 200 OK.
    - El cuerpo es una lista no vacía.
    - Cada elemento contiene al menos las claves 'id' y 'title'.
    """
    response = client.get("/api/modules")
    
    # 1. El estado debe ser estrictamente 200 OK (ya no se acepta 404)
    assert response.status_code == 200, f"Se esperaba 200 pero se obtuvo {response.status_code}: {response.text}"
    
    data = response.json()
    
    # 2. El cuerpo debe ser una lista y no debe estar vacía
    assert isinstance(data, list), "El cuerpo de la respuesta debe ser una lista."
    assert len(data) > 0, "La lista de módulos no puede estar vacía."
    
    # 3. Cada elemento de la lista debe contener las propiedades canónicas mínimas 'id' y 'title'
    for item in data:
        assert isinstance(item, dict), "Cada elemento del catálogo debe ser un objeto/dict."
        assert "id" in item, "El módulo no contiene la clave 'id'."
        assert "title" in item, "El módulo no contiene la clave 'title'."