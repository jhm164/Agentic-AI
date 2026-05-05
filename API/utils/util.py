

def dummy_users_db():
    return  {
            "username": "a",
            "full_name": "John Doe",
            "email": "johndoe@example.com",
            "password": "a",
            "role": "admin"
            }
    


def hotels_list():
    return[
    {
        "id":1,
        "name":"Hotel 1",
        "description":"Hotel 1 description",
        "price":100,
        "availability":True
    },
    {
        "id":2,
        "name":"Hotel 2",
        "description":"Hotel 2 description",
        "price":200,
        "availability":True
    },
    {
        "id":3,
        "name":"Hotel 3",
        "description":"Hotel 3 description",
        "price":300,
        "availability":True
    }
]
