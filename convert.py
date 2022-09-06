#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:
# Copyright (C) 2022 J. Nathanael Philipp (jnphilipp) <nathanael@philipp.land>
# TEI-XML to CoNLL-U converter.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
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
__copyright__ = "Copyright 2019-2022 J. Nathanael Philipp (jnphilipp)"
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
            f"%(prog)s v{__version__}\n{__copyright__}\n"
            "License GPLv3+: GNU GPL version 3 or later "
            "<https://gnu.org/licenses/gpl.html>.\nThis is free software: you are free "
            "to change and redistribute it.\nThere is NO WARRANTY, to the extent "
            f"permitted by law.\n\nReport bugs to {__github__}/issues."
            f"\nWritten by {__author__} <{__email__}>"
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
        parents = dict.fromkeys(
            lxml.etree.parse(xml)
            .getroot()
            .findall(".//{http://www.tei-c.org/ns/1.0}w/..")
        )
        logging.info(f"Found {len(parents):d} sentences.")
        for p in parents.keys():
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
                pos = None
                if e.tag == "{http://www.tei-c.org/ns/1.0}pc":
                    pos = "PUNCT"
                elif "subtype" in e.attrib and e.attrib["subtype"] == "number":
                    pos = "NUM"

                misc = []
                if e.tail != " ":
                    misc.append("SpaceAfter=No")
                if "type" in e.attrib:
                    misc.append(f"Type={e.attrib.get('type')}")
                if "subtype" in e.attrib:
                    misc.append(f"Subtype={e.attrib.get('subtype')}")
                if "orig" in e.attrib:
                    misc.append(f"Orig={e.attrib.get('orig')}")
                if "norm" in e.attrib:
                    misc.append(f"Norm={e.attrib.get('norm')}")
                tokens.append(
                    Token(
                        {
                            "id": i,
                            "form": "".join(e.itertext(with_tail=False)),
                            "lemma": e.attrib.get("lemma"),
                            "upos": pos,
                            "xpos": None,
                            "feats": None,
                            "head": None,
                            "deprel": None,
                            "deps": None,
                            "misc": "|".join(misc) if len(misc) > 0 else None,
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
