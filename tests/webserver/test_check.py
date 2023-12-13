def test_check(web_client):
    url = "/check/"
    rsp = web_client.get(url)
    assert rsp.data.decode() == "ok"
