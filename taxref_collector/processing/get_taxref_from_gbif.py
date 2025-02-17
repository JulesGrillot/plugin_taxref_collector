# Import basic libs
import json

# Import PyQt libs
from qgis.PyQt.QtCore import QObject, QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest


class GetTaxrefFromGBIF(QObject):
    finished_dl = pyqtSignal()
    """Get multiples informations from a getcapabilities request.
    List all layers available, get the maximal extent of all the Wfs' data."""

    def __init__(
        self,
        network_manager=None,
        project=None,
        layer=None,
        dlg=None,
        gbif_id_field=None,
    ):
        super().__init__()
        self.network_manager = network_manager
        self.project = project
        self.layer = layer
        self.thread = dlg.thread
        self.progress_bar = dlg.select_progress_bar_label
        self.gbif_id_field = gbif_id_field
        self._pending_downloads = 0

        self.ids = {}

        for feature in self.layer.getFeatures():
            if feature[self.gbif_id_field] not in self.ids:
                self.ids[feature[self.gbif_id_field]] = [feature.id()]
            else:
                self.ids[feature[self.gbif_id_field]].append(feature.id())
        self._pending_downloads = len(self.ids)
        self._iterate_ids = 0

        self.thread.set_max(len(self.ids))
        self.thread.add_one(0)
        self.progress_bar.setText(
            self.tr("Downloaded data : " + str(0) + "/" + str(len(self.ids)))
        )

        self.download(list(self.ids.keys())[self._iterate_ids])

    @property
    def pending_downloads(self):
        return self._pending_downloads

    @property
    def iterate_ids(self):
        return self._iterate_ids

    def download(self, gbif_id):
        features_id = self.ids[gbif_id]
        url = "https://www.gbif.org/api/species/{gbif_id}/checklistdatasets?limit=100".format(
            gbif_id=gbif_id
        )
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handle_finished(reply, features_id))
        self._iterate_ids += 1

    def handle_finished(self, reply, features_id):
        self._pending_downloads -= 1
        if reply.error() != QNetworkReply.NoError:
            print(f"code: {reply.error()} message: {reply.errorString()}")
            if reply.error() == 403:
                print("Service down")
        else:
            data_request = reply.readAll().data().decode()
            if data_request != "":
                res = json.loads(data_request)
                if "results" in res:
                    for elem in res["results"]:
                        if elem["title"] == "TAXREF":
                            taxref_id = elem["_relatedTaxon"]["taxonID"]
                            taxref_name = elem["_relatedTaxon"]["scientificName"]
                            self.layer.startEditing()
                            for feature_id in features_id:
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
                            print("ERREUR no TAXREF")
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
                    self.download(list(self.ids.keys())[self._iterate_ids])
