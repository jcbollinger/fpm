from distutils.core import Command
import os
import pkg_resources
try:
    import json
except ImportError:
    import simplejson as json


# Note, the last time I coded python daily was at Google, so it's entirely
# possible some of my techniques below are outdated or bad.
# If you have fixes, let me know.


class get_metadata(Command):
    description = "get package metadata"
    user_options = [
        ('load-requirements-txt', 'l',
         "load dependencies from requirements.txt"),
        ]
    boolean_options = ['load-requirements-txt']

    def initialize_options(self):
        self.load_requirements_txt = False
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()
        self.requirements_txt = os.path.join(self.cwd, "requirements.txt")
        # make sure we have a requirements.txt
        if self.load_requirements_txt:
            self.load_requirements_txt = os.path.exists(self.requirements_txt)

    def fix_op(self, op):
        fop = op
        if op == "==":
            fop = "="
        return fop

    def run(self):
        data = {
            "name": self.distribution.get_name(),
            "version": self.distribution.get_version(),
            "author": "%s <%s>" % (
                self.distribution.get_author(),
                self.distribution.get_author_email(),
            ),
            "description": self.distribution.get_description(),
            "license": self.distribution.get_license(),
            "url": self.distribution.get_url(),
        }

        if self.distribution.has_ext_modules():
            data["architecture"] = "native"
        else:
            data["architecture"] = "all"

        final_deps = []

        if self.load_requirements_txt:
            print "processing  requirements.txt, %s" % self.requirements_txt
            for line in open(self.requirements_txt):
                for req in pkg_resources.parse_requirements(line):
                    if req.specs:
                        for spec in req.specs:
                            final_deps.append("%s %s %s" % (req.project_name,
                                self.fix_op(spec[0]), spec[1]))
                    else:
                        final_deps.append(req.project_name)
        else:
            if getattr(self.distribution, 'install_requires', None):
                for dep in pkg_resources.parse_requirements(
                        self.distribution.install_requires):
                    # add all defined specs to the dependecy list separately.
                    if dep.specs:
                        for operator, version in dep.specs:
                                final_deps.append("%s %s %s" %
                                        (dep.project_name,
                                            self.fix_op(operator),
                                            version))
                    else:
                        final_deps.append(dep.project_name)

        data["dependencies"] = final_deps

        if hasattr(json, 'dumps'):
            print(json.dumps(data, indent=2))
        else:
            # For Python 2.5 and Debian's python-json
            print(json.write(data))
