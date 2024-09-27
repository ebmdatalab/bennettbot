import requests

from workspace.workflows import jobs


QUERY = """query latestRun($workflow_database_id: ID!){
    node(id: $workflow_database_id) {
    ... on Workflow {
        databaseId
        runs(first: 1) {
        nodes {
            id
            databaseId
            createdAt
            checkSuite {
            id
            databaseId
            branch {
                name
            }
            status
            conclusion
            }
            }
        }
        }
    }
    }
}"""


def post_request(payload):  # pragma: no cover
    URL = "https://api.github.com/graphql"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {jobs.TOKEN}",
        "GraphQL-Features": "projects_next_graphql",
    }
    rsp = requests.post(URL, headers=HEADERS, json=payload)
    rsp.raise_for_status()
    return rsp.json()


def query_latest_workflow_run(workflow_id):
    variables = {"workflow_database_id": workflow_id}
    payload = {"query": QUERY, "variables": variables}
    return post_request(payload)


def get_latest_check_suite(workflow_id):
    response = query_latest_workflow_run(workflow_id)
    return response["data"]["node"]["runs"]["nodes"][0]["checkSuite"]


class GraphQLReporter(jobs.RepoWorkflowReporter):
    # Use node id instead of workflow id
    def get_workflows(self) -> dict:
        results = self._get_json_response("actions/workflows")["workflows"]
        workflows = {wf["node_id"]: wf["name"] for wf in results}
        if self.branch is not None and self.branch == "main":
            self.remove_workflows_skipped_on_main(workflows)
        return workflows
