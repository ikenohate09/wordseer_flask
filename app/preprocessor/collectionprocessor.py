"""This file has tools to process a collection of files. This is the interface
between the input and the pipeline.
"""

from datetime import datetime
import logging
import os

from app import app
import database
from . import logger
from .documentparser import DocumentParser
from .sequenceprocessor import SequenceProcessor
from . import structureextractor
from .stringprocessor import StringProcessor
from . import counter

from app.models import Document, Base

class CollectionProcessor(object):
    """Process a collection of files.
    """
    def __init__(self):
        self.str_proc = StringProcessor()
        self.pylogger = logging.getLogger(__name__)

    def process(self, collection_dir, docstruc_filename,
        filename_extension, start_from_scratch):
        """
        This function relies on several methods to:

        1. Set up the database if necessary
        2. Extract metadata, populate the narratives, sentences, and paragraphs
            tables
        3. Process the sentences by tokenizing and indexing the words
        4. Process the sentences by performing grammatical parsing

        :param str collection_dir: The directory whose files should be
            processed.
        :param str docstructure_file_name: The name of the JSON file that
            describes the structure in the document files.
        :param str file_name_extension: Files with this extension will be parsed
            as documents.
        :param boolean start_from_scratch: If true, then the tables in the
            database will be recreated.
        """

        Base.commit_on_save = False

	    # Set up database if necessary
        if start_from_scratch is True:
            database.reset()

        # Extract metadata, populate documents, sentences, and doc structure
        # tables
        if not "true" in logger.get("finished_recording_text_and_metadata"):
            self.pylogger.info("Extracting document text and metadata")
            self.extract_record_metadata(collection_dir,
                docstruc_filename, filename_extension)

        # Parse the documents
        if ((app.config["GRAMMATICAL_PROCESSING"] or
            (app.config["WORD_TO_WORD_SIMILARITY"] and
            app.config["PART_OF_SPEECH_TAGGING"])) and not
            "true" in logger.get("finished_grammatical_processing").lower()):
            self.pylogger.info("Parsing documents")
            self.parse_documents()
            self.pylogger.info("Parsing documents")

        # Calculate word-in-sentence counts and TF-IDFs
        if not "true" in logger.get("word_counts_done").lower():
            self.pylogger.info("Calculating word counts")
            # TODO: implement a method to do word counts for sentences
            logger.log("word_counts_done", "true", logger.REPLACE)

        # Calculate word TFIDFs
        if not "true" in logger.get("tfidf_done").lower():
            self.pylogger.info("Calculating TF IDF's")
            # TODO: implement tfidf method in document

        # Calculate word-to-word-similarities
        if (app.config["WORD_TO_WORD_SIMILARITY"] and not
            "true" in logger.get("word_similarity_calculations_done")):
            self.pylogger.info("Calculating Lin Similarities")
            # TODO: implement similarities

    def extract_record_metadata(self, collection_dir, docstruc_filename,
        filename_extension):
        """Extract metadata from each file in collection_dir, and populate the
        documents, sentences, and document structure database tables.

        For every document file in ``collection_dir``, this extracts any
        documents from it using the
        :class:`~wordseerbackend.structureextractor.StructureExtractor`
        and the provided ``docstruc_filename``.

        Then, every document extracted is recorded with
        ``create_new_document`` from the reader/writer. Once all documents
        have been extracted, ``finished_recording_text_and_metadata`` is set to
        ``true`` using the :mod:`~wordseerbackend.logger`.

        :param StringProcessor str_proc: An instance of StringProcessor
        :param str collection_dir: The directory from which files should be
            parsed.
        :param str docstruc_file_name: A JSON description of the
            document structure.
        :param str filename_extension: The extension of the files that contain
            documents.
        """
        extractor = structureextractor.StructureExtractor(self.str_proc,
            docstruc_filename)

        # Extract and record metadata, text for documents in the collection
        num_files_done = 1
        contents = []
        for filename in os.listdir(collection_dir):
            if (os.path.splitext(filename)[1].lower() ==
                filename_extension.lower()):
                contents.append(filename)

        docs = [] # list of Documents

        for filename in contents:
            if (not "[" + str(num_files_done) + "]" in
                logger.get("text_and_metadata_recorded") and not
                filename[0] == "."):
                logger.log("finished_recording_text_and_metadata", "false",
                    logger.REPLACE)

                start_time = datetime.now()
                docs = extractor.extract(os.path.join(collection_dir,
                    filename))
                seconds_elapsed = (datetime.now() - start_time).total_seconds()

                self.pylogger.info("Time to extract and record metadata: %ss",
                    seconds_elapsed)

                self.pylogger.info("%s/%s %s", str(num_files_done),
                    str(len(contents)), filename)
                logger.log("text_and_metadata_recorded",
                    str(num_files_done), logger.UPDATE)


            num_files_done += 1

        logger.log("finished_recording_text_and_metadata", "true",
            logger.REPLACE)

    def parse_documents(self):
        """Parse documents in the database using
        :meth:`~wordseerbackend.parser.documentparser.DocumentParser.parse_document`.

        Given the documents already loaded into the database from
        :meth:`~wordseerbackend.collectionprocessor.CollectionProcessor.extract_record_metadata`,
        parse each document using
        :meth:`~wordseerbackend.parser.documentparser.DocumentParser.parse_document`.
        Afterwards, call ``finish_grammatical_processing`` on the reader/writer.
        """

        documents = Document.query.all()
        document_parser = DocumentParser(self.str_proc)
        documents_parsed = 0
        document_count = len(documents)
        latest = logger.get("latest_parsed_document_id")

        if len(latest) == 0:
            latest = "0"

        latest_id = int(latest)

        for document in documents:
            if document.id > latest_id:
                self.pylogger.info("Parsing document %s/%s",
                    str(documents_parsed), str(document_count))
                start_time = datetime.now()
                document_parser.parse_document(document)
                seconds_elapsed = (datetime.now() - start_time).total_seconds()
                self.pylogger.info("Time to parse document: %ss",
                    str(seconds_elapsed))
                logger.log("finished_grammatical_processing", "false",
                    logger.REPLACE)
                logger.log("latest_parsed_document_id", str(document.id),
                    logger.REPLACE)

            documents_parsed += 1

        counter.count()

