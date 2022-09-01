#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:
"""TEI-XML to CoNLL-U converter."""

from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    FileType,
    RawDescriptionHelpFormatter,
)
from conllu import Token, TokenList
from typing import List

import logging
import lxml.etree
import sys


__author__ = "J. Nathanael Philipp"
__email__ = "nathanael@philipp.land"
__license__ = "GPLv3"
__version__ = "0.1.0"
__github__ = "https://github.com/jnphilipp/tei-to-conll-u-converter"


class ArgFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    """Combination of ArgumentDefaultsHelpFormatter and RawDescriptionHelpFormatter."""

    pass


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="tei-to-conll-u-converter", formatter_class=ArgFormatter
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=(
            f"%(prog)s v{__version__}\nReport bugs to {__github__}/issues.\n"
            f"Written by {__author__} <{__email__}>"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="verbosity level; multiple times increases the level, the maximum is 2.",
    )
    parser.add_argument(
        "-f",
        "--log-format",
        default="%(asctime)s [%(levelname)s] %(message)s",
        help="logging format.",
    )
    parser.add_argument(
        "XML",
        nargs="+",
        type=FileType("rb"),
        help="TEI-XML corpora file(s)",
    )
    args = parser.parse_args()

    if args.verbose == 0:
        level = logging.WARN
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        format=args.log_format,
        level=level,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    for xml in args.XML:
        logging.info(f"Start convertion of {xml.name}.")
        sentences: List[TokenList] = []
        parents = set(
            lxml.etree.parse(xml)
            .getroot()
            .findall(".//{http://www.tei-c.org/ns/1.0}w/..")
        )
        logging.info(f"Found {len(parents):d} sentences.")
        for p in parents:
            logging.debug(f"Parsing words from {p.tag}.")
            tokens = TokenList(metadata={"sent_id": len(sentences) + 1})
            i = 0
            for e in p.iter():
                logging.debug(f"Found {e.tag} with {e.text}.")
                if e.tag not in [
                    "{http://www.tei-c.org/ns/1.0}w",
                    "{http://www.tei-c.org/ns/1.0}pc",
                ]:
                    logging.debug(f"Skipping {e.tag}.")
                    continue
                tokens.append(
                    Token(
                        {
                            "id": i,
                            "form": "".join(e.itertext(with_tail=False)),
                            "lemma": e.attrib.get("lemma"),
                            "upos": "PUNCT"
                            if e.tag == "{http://www.tei-c.org/ns/1.0}pc"
                            else None,
                            "xpos": None,
                            "feats": None,
                            "head": None,
                            "deprel": None,
                            "deps": None,
                            "misc": None if e.tail == " " else "SpaceAfter=No",
                        }
                    )
                )
                logging.debug(f"Added {tokens[-1]['form']} as {i:d}. token.")
                i += 1
            tokens[-1]["misc"] = None
            text = ""
            for t in tokens:
                text += t["form"] + (" " if not t["misc"] == "SpaceAfter=No" else "")
            tokens.metadata["text"] = text.strip()
            sentences.append(tokens)
            logging.debug(f"Added {text} as {len(sentences)}. sentence.")
        logging.info(f"Converted {len(sentences):d} sentences.")
        logging.info(f"Saving results to {xml.name.replace('.xml', '.conll')}.")
        with open(xml.name.replace(".xml", ".conllu"), "w", encoding="utf8") as f:
            f.write("\n".join([s.serialize() for s in sentences]))
