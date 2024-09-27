# from workspace.workflows import graphql

RESULTS = {
    "MDg6V29ya2Zsb3cyMzkzMjI0": {
        "data": {
            "node": {
                "databaseId": 2393224,
                "runs": {
                    "nodes": [
                        {
                            "id": "WFR_kwLOEB6Igc8AAAAClAeHkw",
                            "databaseId": 11073456019,
                            "createdAt": "2024-09-27T15:31:44Z",
                            "checkSuite": {
                                "id": "CS_kwDOEB6Igc8AAAAGvOUDog",
                                "databaseId": 28938929058,
                                "branch": {
                                    "name": "madwort-and-providence/full-job-id-matching"
                                },
                                "status": "COMPLETED",
                                "conclusion": "FAILURE",
                            },
                        }
                    ]
                },
            }
        },
        "extensions": {
            "warnings": [
                {
                    "type": "DEPRECATION",
                    "message": "The id MDg6V29ya2Zsb3cyMzkzMjI0 is deprecated. Update your cache to use the next_global_id from the data payload.",
                    "data": {
                        "legacy_global_id": "MDg6V29ya2Zsb3cyMzkzMjI0",
                        "next_global_id": "W_kwDOEB6Igc4AJISI",
                    },
                    "link": "https://docs.github.com",
                }
            ]
        },
    },
    "W_kwDOEB6Igc4AGLK3": {
        "data": {
            "node": {
                "databaseId": 1618615,
                "runs": {
                    "nodes": [
                        {
                            "id": "WFR_kwLOEB6Igc8AAAACcRa6kw",
                            "databaseId": 10487249555,
                            "createdAt": "2024-08-21T09:28:29Z",
                            "checkSuite": {
                                "id": "CS_kwDOEB6Igc8AAAAGYlekdg",
                                "databaseId": 27419714678,
                                "branch": {"name": "main"},
                                "status": "COMPLETED",
                                "conclusion": "SUCCESS",
                            },
                        }
                    ]
                },
            }
        }
    },
}
