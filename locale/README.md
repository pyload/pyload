# Localization

The localization process take place on Crowdin:

http://translate.pyload.org

or

http://crowdin.net/project/pyload

## Add a tip for translators
If you want to explain a translatable string to make the translation process easier you can do that using comment block starting with `L10N:`. For example:

```python
# L10N: Here the tip for translators
# Thanks
print(_("A translatable string"))
```

Translators will see:

```
L10N: Here the tip for translators
Thanks
```

## Updating templates

To update POT files run:

`paver generate_locale`

to automatically upload the updated POTs on Crowdin for the localization process just run:

`paver upload_translations -k [api_key]`

the API Key can be retrieved in the Settings panel of the project on Crowdin.

## Retrieve updated PO files

Updated PO files can be automatically download from Crowdin using:

`paver download_translations -k [api_key]`

This is allowed only to administrators, users can download the last version of the translations using the Crowdin web interface.

## Compile PO files

MO files can be generated using:

`paver compile_translations`

To compile a single file just use `msgfmt`. For example to compile a core.po file run:

`msgfmt -o core.mo core.po`
