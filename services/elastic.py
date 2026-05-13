from elasticsearch import Elasticsearch
from datetime import datetime
from logger import log
from config import ES_API, INDEX_NAME


class ElasticsearchService:

    def __init__(self):

        try:

            log.info(
                f"Connecting Elasticsearch => {ES_API}"
            )

            # Elasticsearch Client
            self.es = Elasticsearch(
                ES_API,
                request_timeout=30,
                retry_on_timeout=True
            )

            self.index = INDEX_NAME

            # Test Connection
            info = self.es.info()

            log.info(
                f"Connected Elasticsearch => {info['cluster_name']}"
            )

            self.create_index()

        except Exception as e:

            log.error(
                f"Elasticsearch init failed: {str(e)}",
                exc_info=True
            )

            raise Exception(
                "Elasticsearch initialization failed"
            )

    # ======================================================
    # CREATE INDEX
    # ======================================================
    def create_index(self):

        try:

            if self.es.indices.exists(index=self.index):

                log.info(
                    f"Index already exists => {self.index}"
                )

                return

            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {
                            "type": "date",
                            "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
                        },
                        "agentId": {
                            "type": "keyword"
                        },
                        "macAddress": {
                            "type": "keyword"
                        },
                        "level": {
                            "type": "keyword"
                        },
                        "thread": {
                            "type": "keyword"
                        },
                        "message": {
                            "type": "text"
                        },
                        "url": {
                            "type": "keyword"
                        },
                        "exception": {
                            "properties": {
                                "type": {
                                    "type": "keyword"
                                },
                                "stack_trace": {
                                    "type": "text"
                                }
                            }
                        }
                    }
                }
            }

            self.es.indices.create(
                index=self.index,
                body=mapping
            )

            log.info(
                f"Index created => {self.index}"
            )

        except Exception as e:

            log.error(
                f"Index creation failed: {str(e)}",
                exc_info=True
            )

    # ======================================================
    # SANITIZE LOG
    # ======================================================
    def sanitize_log(self, data: dict):

        clean_data = {
            "timestamp": str(data.get("timestamp") or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")).replace(" ", "T"),

            "agentId": data.get("agentId", ""),
            "macAddress": data.get("macAddress", ""),
            "level": data.get("level", "INFO"),
            "thread": data.get("thread", ""),
            "message": data.get("message", ""),
            "url": data.get("url", ""),

            "exception": {
                "type": "",
                "stack_trace": ""
            }
        }

        if isinstance(data.get("exception"), dict):

            clean_data["exception"]["type"] = \
                data["exception"].get("type", "")

            stack = data["exception"].get(
                "stack_trace",
                ""
            )

            if isinstance(stack, list):
                stack = "\n".join(stack)

            clean_data["exception"]["stack_trace"] = stack

        return clean_data

    # ======================================================
    # INSERT LOG
    # ======================================================
    def insert_log(self, data: dict):

        try:

            clean_data = self.sanitize_log(data)

            response = self.es.index(
                index=self.index,
                document=clean_data
            )

            log.info(
                f"Log inserted => {response['_id']}"
            )

            return {
                "inserted": True,
                "document_id": response["_id"]
            }

        except Exception as e:

            log.error(
                f"Insert log failed: {str(e)}",
                exc_info=True
            )

            return {
                "inserted": False,
                "error": str(e)
            }

    # ======================================================
    # FETCH LOGS
    # ======================================================
    def fetch_logs(self, page=1, size=100):

        try:

            start = (page - 1) * size

            response = self.es.search(
                index=self.index,
                body={
                    "query": {
                        "match_all": {}
                    },
                    "from": start,
                    "size": size,
                    "sort": [
                        {
                            "timestamp": {
                                "order": "desc"
                            }
                        }
                    ]
                }
            )

            logs = [
                hit["_source"]
                for hit in response["hits"]["hits"]
            ]

            return {
                "total": response["hits"]["total"]["value"],
                "page": page,
                "size": size,
                "logs": logs
            }

        except Exception as e:

            log.error(
                f"Fetch logs failed: {str(e)}",
                exc_info=True
            )

            raise Exception(
                "Unable to fetch logs"
            )

    # ======================================================
    # SEARCH LOGS
    # ======================================================
    def search_logs(
        self,
        agentId=None,
        macAddress=None,
        level=None,
        start_date=None,
        end_date=None,
        page=1,
        size=100
    ):

        try:

            start = (page - 1) * size

            must_queries = []

            if agentId:

                must_queries.append({
                    "term": {
                        "agentId": agentId
                    }
                })

            if macAddress:

                must_queries.append({
                    "term": {
                        "macAddress": macAddress
                    }
                })

            if level:

                must_queries.append({
                    "term": {
                        "level": level
                    }
                })

            if start_date or end_date:

                range_query = {
                    "range": {
                        "timestamp": {}
                    }
                }

                if start_date:
                    range_query["range"]["timestamp"]["gte"] = start_date

                if end_date:
                    range_query["range"]["timestamp"]["lte"] = end_date

                must_queries.append(range_query)

            query = {
                "bool": {
                    "must": must_queries
                    if must_queries
                    else [{"match_all": {}}]
                }
            }

            response = self.es.search(
                index=self.index,
                body={
                    "query": query,
                    "from": start,
                    "size": size,
                    "sort": [
                        {
                            "timestamp": {
                                "order": "desc"
                            }
                        }
                    ]
                }
            )

            logs = [
                hit["_source"]
                for hit in response["hits"]["hits"]
            ]

            return {
                "total": response["hits"]["total"]["value"],
                "page": page,
                "size": size,
                "logs": logs
            }

        except Exception as e:

            log.error(
                f"Search logs failed: {str(e)}",
                exc_info=True
            )

            raise Exception(
                "Unable to search logs"
            )