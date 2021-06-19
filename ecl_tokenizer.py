# -*- coding: utf-8 -*-
# Ecl tokenizer.
# by Baurzhan Muftakhidinov

import os
import re
from difflib import HtmlDiff

sections = ("RUNSPEC", "GRID", "EDIT", "PROPS", "REGIONS", "SOLUTION", "SUMMARY", "SCHEDULE")

kwd_expr = re.compile("^[A-Z][A-Z0-9]+[\+\-]?$")

class EclKwd:
    def __init__(self, name, section, parent, line_no, value=None):
        #print("EclKwd init with data: {0}".format(value))
        self.name     = name
        self.value    = value
        self.section  = section
        self.parent   = parent
        self.line_num = line_no

    def to_list(self, expand=True):
        # Grid keyword values to list of lists.
        out       = []
        push_line = False
        line_buf  = []   # Corresponds to 1 data record.
        if not self.value:
            return out
        for line in self.value:
            line = line.strip()
            if line.endswith("/"):
                line = line[0:-1]
                push_line = True
            line = line.split()
            for elem in line:
                if "*" in elem and expand:
                    num, val = elem.split("*")
                    line_buf.extend(int(num) * [val])
                else:
                    line_buf.append(elem)
            if push_line:  # end of record.
                if line_buf:
                    out.append(line_buf)
                push_line = False
                line_buf = []
        return out

    def __repr__(self):
        return '<EclKwd: {0:9} Section "{1:9}" Parent: "{2}" Line_number: "{3}">\n'.format(self.name, self.section, self.parent, self.line_num)

class EclCase:
    def __init__(self, data_file, verbose=False, skip_grdecl=False):
        print(f"INFO: EclCase init from data deck: {data_file}")
        self.data_file       = data_file
        self.skip_grdecl     = skip_grdecl
        self.processed_files = []
        self.missing_files   = []
        self.keywords        = []
        self.parse(data_file, verbose=verbose)

    def __repr__(self):
        title = ""
        if self.has_kwd("TITLE"):
            title_data = self.get_kwds("TITLE")[0].value
            if title_data:
                title = self.get_kwds("TITLE")[0].value[0].strip()
        return '<EclCase: Title: `{0}` Keywords: {1} Includes: {2}, missing: {3}, File: "{4}">\n'.format(title, len(self.keywords), len(self.processed_files), len(self.missing_files), self.data_file)

    def parse(self, in_file, cur_section="", verbose=False):
        if self.skip_grdecl and in_file.toupper().endswith(".GRDECL"):
            if verbose:
                print("SKIP: Skipping grid files was requested!")
            return
        in_file = os.path.abspath(in_file).strip()
        if verbose:
            print("INFO: Parsing file: {0}".format(in_file))
        self.processed_files.append(in_file)
        last_kwd = None
        buf = []
        line_no = 0
        line = ""

        # TODO: which encoding should DATA file have?
        with open(in_file, 'r') as sr:
            line      = sr.readline()
            line_no   = 0
            buf       = []
            probe_kwd = ""
            last_kwd  = None
            while line:
                line_no += 1
                line=line.rstrip()
                # We found comment.
                if "--" in line:
                    line = line.split("--")[0]
                # We found empty line.
                if not line.strip():
                    line = sr.readline()
                    continue
                if len(line) >= 8 and not "/" in line:
                    probe_kwd = line[:8].rstrip()
                else:
                    probe_kwd = line
                # Check for TITLE keyword data.
                if last_kwd and last_kwd.name == "TITLE":
                    last_kwd.value = [line]
                    self.keywords.append(last_kwd)
                    last_kwd = None
                    line = sr.readline()
                    continue
                # Looks like we found a keyword.
                if probe_kwd and kwd_expr.match(probe_kwd):
                    if probe_kwd in sections:
                        cur_section = probe_kwd
                    if last_kwd:
                        last_kwd.value = buf.copy()
                        self.keywords.append(last_kwd)
                        if last_kwd.name == "INCLUDE":
                            self.parse_include(last_kwd, verbose=verbose)
                        buf.clear()
                    if verbose:
                        print("DBG : keyword found: ", probe_kwd, " line: ", line_no)
                    last_kwd = EclKwd(probe_kwd, cur_section, in_file, line_no)
                else:
                    if not last_kwd:
                        raise ValueError("Data line without previous keyword is found! ", line_no, line)
                    buf.append(self.process_data_line(line))
                line = sr.readline()
        if last_kwd and last_kwd not in self.keywords:
            last_kwd.value = buf.copy()
            self.keywords.append(last_kwd)
            if last_kwd.name == "INCLUDE":
                self.parse_include(last_kwd, verbose=verbose)
            buf.clear()

    def parse_include(self, ecl_kwd, verbose=False):
        if not ecl_kwd.value:
            print("ERR : The keyword supplied to parse_include does not have a value in it.")
            return
        inc_file = ecl_kwd.value[0].replace("'", "").strip().strip("/").strip()
        included_file_name = os.path.abspath(os.path.join(os.path.dirname(self.data_file), inc_file)).strip()
        if included_file_name in self.processed_files:
            if verbose:
                print("INFO: Duplicated INCLUDE found at {0}:{1} : {2}".format(ecl_kwd.parent, ecl_kwd.line_num, included_file_name))
        else:
            if os.path.exists(included_file_name):
                self.parse(included_file_name, ecl_kwd.section, verbose=verbose)
            else:
                print("ERR : INCLUDE file not found, ref file: {0}, line: {1}, name: {2}".format(ecl_kwd.parent, ecl_kwd.line_num, included_file_name))
                self.missing_files.append(included_file_name)

    def strip_complex_comment(self, line):
        # Complex comments not having `--` and located after closing slash.
        within_quote=False
        for pos, char in enumerate(line):
            if char == "'":
                if not within_quote:
                    within_quote = True
                else:
                    within_quote = False
            elif char == "/":
                if not within_quote:
                    return line[0:pos+1]
        return line

    def process_data_line(self, line):
        # From manual. Comments could be directly included after the '/', without the '--'.
        # By this time, we stripped the right part of any '--' delimiters.
        line = line.rstrip()
        # Line has a slash, whether data closing or inside include paths.
        if "/" in line:
            if "'" in line:
                line = self.strip_complex_comment(line)
            else:
                bs_pos = line.find("/")
                line = line[0:bs_pos+1]
                # We preserve the backslash itself to keep records.
        return line
    
    def has_kwd(self, keyword):
        # Whether case has keyword.
        for kwd in self.keywords:
            if kwd.name == keyword:
                return True
        return False

    def get_kwds(self, keyword):
        # Returns keywords found by name supplied.
        out = []
        for kwd in self.keywords:
            if kwd.name == keyword:
                out.append(kwd)
        return out

    def get_kwds_data(self, keyword, expand=True):
        # Returns combined data of all instances of keyword.
        out = []
        for kwd in self.get_kwds(keyword):
            out.extend(kwd.to_list(expand=expand))
        return out

    def describe(self):
        print("+", self.data_file)
        for pfile in self.processed_files:
            print("|--", pfile)
        for mfile in self.missing_files:
            print("|XX", mfile)

    def get_top_dir(self):
        # Return the top-most common path of all files.
        return os.path.commonpath(self.processed_files + self.missing_files)

    def compare_includes_html(self, other):
        # Create file hightlighting differences.
        # Useful for IPython.
        # If needs to be saved, use following snippet:
        #
        # diff = case.compare_includes_html(other_case)
        # with open("output.html", "w+") as file:
        #     file.save(diff)
        #
        diff = HtmlDiff().make_file(self.processed_files, other.processed_files, self.data_file, other.data_file)
        return diff

if __name__ == "__main__":
    print("Import me!")

