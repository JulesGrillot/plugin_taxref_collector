# Import basic libs
import json

# Import PyQt libs
from qgis.PyQt.QtCore import QObject, QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest


class GetTaxrefFromCLB(QObject):
    finished_dl = pyqtSignal()
    """Get multiples informations from a getcapabilities request.
    List all layers available, get the maximal extent of all the Wfs' data."""

    def __init__(
        self,
        network_manager=None,
        project=None,
        layer=None,
        dlg=None,
        field_name=None,
        field_rank=None,
    ):
        super().__init__()
        self.network_manager = network_manager
        self.project = project
        self.layer = layer
        self.thread = dlg.thread
        self.progress_bar = dlg.select_progress_bar_label
        self.field_name = field_name
        self.field_rank = field_rank
        self._pending_downloads = 0

        self.ids = []
        self.names = []
        self.rank = []

        for obs in self.layer.getFeatures():
            self.ids.append(obs.id())
            self.names.append(obs[obs[self.field_rank].lower()])
            self.rank.append(obs[self.field_rank])
        self._pending_downloads = len(self.names)
        self._iterate_names = 0

        self.thread.set_max(len(self.ids))
        self.thread.add_one(0)
        self.progress_bar.setText(
            self.tr("Downloaded data : " + str(0) + "/" + str(len(self.ids)))
        )

        self.download(self.ids[self._iterate_names], self.rank[self._iterate_names])

    @property
    def pending_downloads(self):
        return self._pending_downloads

    @property
    def iterate_names(self):
        return self._iterate_names

    def download(self, feature_id, rank):
        if rank.lower() == "stateofmatter":
            self._iterate_names += 1
            self.download(self.ids[self._iterate_names], self.rank[self._iterate_names])
        else:
            feature = self.layer.getFeature(feature_id)
            if rank.lower() == "complex" or rank.lower() == "hybrid":
                rank = "species"
            elif rank.lower() == "epifamily" or rank.lower() == "section":
                rank = "genus"
            elif rank.lower() == "subtribe":
                rank = "family"
            name = feature[rank]
            url = "https://api.checklistbank.org/nameusage/search?content=SCIENTIFIC_NAME&datasetKey=2008&facet=datasetKey&facet=rank&facet=issue&facet=status&facet=nomStatus&facet=nameType&facet=field&facet=authorship&facet=authorshipYear&facet=extinct&facet=environment&facet=origin&limit=50&offset=0&q={name}&rank={rank}&status=accepted&type=PREFIX".format(  # noqa: E501
                name=name, rank=rank.lower()
            )
            request = QNetworkRequest(QUrl(url))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            reply = self.network_manager.get(request)
            reply.finished.connect(lambda: self.handle_finished(reply, feature_id))
            self._iterate_names += 1

    def handle_finished(self, reply, feature_id):
        self._pending_downloads -= 1
        if reply.error() != QNetworkReply.NoError:
            print(f"code: {reply.error()} message: {reply.errorString()}")
            if reply.error() == 403:
                print("Service down")
        else:
            data_request = reply.readAll().data().decode()
            if data_request != "":
                res = json.loads(data_request)
                if res["total"] == 1:
                    if "result" in res:
                        taxref_id = res["result"][0]["id"]
                        taxref_name = res["result"][0]["usage"]["label"]
                        self.layer.startEditing()
                        self.layer.changeAttributeValue(
                            feature_id,
                            self.layer.fields().indexFromName("cd_nom"),
                            taxref_id,
                        )
                        self.layer.changeAttributeValue(
                            feature_id,
                            self.layer.fields().indexFromName("taxref_name"),
                            taxref_name,
                        )
                        self.layer.changeAttributeValue(
                            feature_id,
                            self.layer.fields().indexFromName("taxref_url"),
                            "https://inpn.mnhn.fr/espece/cd_nom/{cd_nom}".format(
                                cd_nom=taxref_id
                            ),
                        )
                        self.layer.commitChanges()
                        self.layer.triggerRepaint()
                else:
                    print(res)
                if self.pending_downloads == 0:
                    self.project.addMapLayer(self.layer)
                    self.finished_dl.emit()
                else:
                    self.thread.set_max(len(self.ids))
                    self.thread.add_one(1)
                    self.progress_bar.setText(
                        self.tr(
                            "Downloaded data : "
                            + str(self.thread.value)
                            + "/"
                            + str(len(self.ids))
                        )
                    )
                    self.download(
                        self.ids[self._iterate_names], self.rank[self._iterate_names]
                    )
