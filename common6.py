
def NER_contrato_text(df, text, contract_text_path):
    #Function that performs 

    import pandas as pd
    import logging
    from io import StringIO 
    import os
    
    import boto3
    from botocore.exceptions import ClientError
    import time
    
    ## Bucket de Alexis
    aws_access_key_id="AKIAZ7JA337WYTRP5TVZ"
    aws_secret_access_key="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"
    region_name = "us-east-2"
    bucket = "bootcampaws315"
    
    uid = contract_text_path.split("/")[0]
    document_name = contract_text_path.split("/")[1][:-4]
    #key=uid + '/' + document_name + '.csv'
    key2=uid + '/' + document_name + '.html'
    
    print(f'Working on UUID:   {uid}')
    print(f'Working on document:   {contract_text_path}')  
    
    # NER FUNCTION

    import es_core_news_sm # Spanish model small
    nlp = es_core_news_sm.load()
    
    import re
    from unicodedata import normalize

    def formatingText(text):
        text = text.lower()
        text = re.sub('<.*?>', '', text)
        #text = re.sub(':.*?:', '', text)
        text = re.sub(r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", normalize( "NFD", text), 0, re.I)
        #text = normalize( 'NFC', text)
        #text = re.sub('[^a-z ]', '', text)
        return text
    
    text=formatingText(text)
    
    # spaCy
    doc = nlp(text)
    
    # Customized sentence splitting
    nlp = es_core_news_sm.load()
    boundary = re.compile('^[0-9]$')
    numero = re.compile(r'No')

    def custom_seg(doc):
        prev = doc[0].text
        length = len(doc)
        for index, token in enumerate(doc):
            if (token.text == '.' and boundary.match(prev) and index!=(length - 1)):
                doc[index+1].sent_start = False
            if (token.text == '.' and numero.match(prev) and index!=(length - 1)):
                doc[index+1].sent_start = False    
            prev = token.text
        return doc

    nlp.add_pipe(custom_seg, before='parser')

    #sbd = nlp.create_pipe('sentencizer')
    #nlp.add_pipe(sbd)

    doc = nlp(text)
    
    # Creating list of strings
    sent_list=[sentence.string.strip() for sentence in doc.sents]
    
    # Creating dataframe of sentences
    sent_df = pd.DataFrame({'sentences':sent_list})
    #print (sent_df)
    
    # Token Matcher
    from spacy.matcher import Matcher
    
    # DATE Matcher
    # Matcher Function
    def create_date_patterns():
        date_patterns = [ 
        [{'TEXT': {'REGEX': '(0[1-9]|[12]\d|3[01])\/(0[1-9]|1[0-2])\/([12]\d{3})'}}],
        [{'TEXT': {'REGEX': '([1-9]|0[1-9]|[12]\d|3[01])\/(0[1-9]|1[0-2])\/([1-9]\d{1})'}}],
        
        [{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"POS":"NUM"},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"POS":"NUM"},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"POS":"NUM"},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"POS":"NUM"},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"SHAPE":"dddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"}, {"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"d.ddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"d.ddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"}, {"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"}, {"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"SHAPE":"dd.dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dd.dd.dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dddd-dd-dd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dd-dd-dddd"}, {"LOWER":")"}],
        [{"SHAPE":"dddd-dd-dd"}],
        [{"SHAPE":"dd-dd-dddd"}]
        ]  
        
        return date_patterns
    
    date_matcher = Matcher(nlp.vocab)
    date_matcher.add("DATE", None, *create_date_patterns())
    
    doc = nlp(text)
    doc.ents = []
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in date_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="DATE")

        # Overwrite the doc.ents and add the span
        #doc.ents = [span]
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "DATE"])
    
    # Define the custom component
    def date_component(doc):
        # Apply the matcher to the doc
        matches = date_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="DATE") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    nlp.add_pipe(date_component, after="ner")
    #print(nlp.pipe_names)
    
    from spacy import displacy
    #displacy.render(doc, style="ent")  
    
    nlp.remove_pipe('ner')
    
    date_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "DATE"]
    date_extracted = []
    for i in range(len(date_list)):
        date_ent = date_list[i][0]
        date_extracted.append(date_ent)
    
    date_extracted_df = pd.DataFrame(date_extracted, columns=["date_extracted"])
    #date_extracted_df.to_csv('date_extracted.csv', index=False)

    # ID Matcher
    # Matcher Function
    def create_id_patterns():
        id_patterns = [ 
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"es"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no"}, {"IS_PUNCT":True, "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"},{"LOWER":"numero"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"},{"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"no"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"n"}, {"LOWER":"°"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"n"}, {"LOWER":"°"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"nro"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"no", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NOUN"}],
        [ {"LOWER":"numero"}, {"LOWER":"de"}, {"LOWER":"cedula"},  {"LOWER":"no", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"n°"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cc"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c."}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"LOWER":"c.c.no"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"SHAPE":"x.xd.ddd.ddd"}],
        [{"SHAPE":"x.xdd.ddd.ddd"}],
        [{"SHAPE":"x.xddd.ddd.ddd"}],
        [{"SHAPE":"x.xd.ddd.ddd.ddd"}],
        [{"SHAPE":"x.x.d.ddd.ddd"}],
        [{"SHAPE":"x.x.dd.ddd.ddd"}],
        [{"SHAPE":"x.x.ddd.ddd.ddd"}],
        [{"SHAPE":"x.x.d.ddd.ddd.ddd"}],
        
        [{"LOWER":"doc"},  {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NOUN"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"n°", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"numero"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"numero"},{"SHAPE":"dd.ddd.ddd"}],
        [{"LOWER":"cedula"}, {"LOWER":":",  "OP": "?"}, {"LOWER":"n°"},{"SHAPE":"dd.ddd.ddd"}]
        ]
    
        return id_patterns

    id_matcher = Matcher(nlp.vocab)
    id_matcher.add("ID", None, *create_id_patterns())
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in id_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="ID_NUMBER")

        # Overwrite the doc.ents and add the span
        #doc.ents = [span]
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ID_NUMBER"])
    
    # Define the custom component
    def id_component(doc):
        # Apply the matcher to the doc
        matches = id_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="ID_NUMBER") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(id_component, after="date_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    id_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ID_NUMBER"]
    id_extracted = []
    for i in range(len(id_list)):
        id_ent = id_list[i][0]
        id_extracted.append(id_ent)
    
    id_extracted_df = pd.DataFrame(id_extracted, columns=["id_extracted"])
    #id_extracted_df.to_csv('id_extracted.csv', index=False)

    # PHRASE MATCHER
    from spacy.matcher import PhraseMatcher
    
    # NAME Matcher
    name_matcher = PhraseMatcher(nlp.vocab)
    
    nombres = pd.read_csv('lista_nombres_refiltrados_simple.csv')
    nombre_list=nombres['nombres']
    nombre_patterns = list(nlp.pipe(nombre_list.values))
    
    name_matcher.add("PERSON", None, *nombre_patterns)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in name_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="PERSON")

        # Overwrite the doc.ents and add the span
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "PERSON"])
    
    # Define the custom component REMOVING OVERLAPPED SPANS
    def name_component(doc):
        # Apply the matcher to the doc
        matches = name_matcher(doc)
        
        new_entities = []
        seen_tokens = set()
        entities = doc.ents
        
        for match_id, start, end in matches:
            # check for end - 1 here because boundaries are inclusive
            if start not in seen_tokens and end - 1 not in seen_tokens:
                new_entities.append(Span(doc, start, end, label=match_id))
                entities = [
                    e for e in entities if not (e.start < end and e.end > start)
                ]
                seen_tokens.update(range(start, end))
        
        doc.ents = tuple(entities) + tuple(new_entities) 
            
        # Create a Span for each match and assign the label "PERSON"
        #spans = [Span(doc, start, end, label="PERSON") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        #doc.ents = list(doc.ents) + spans
        
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(name_component, after="id_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    person_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "PERSON"]
    person_extracted = []
    for i in range(len(person_list)):
        person_ent = person_list[i][0]
        person_extracted.append(person_ent)
    
    person_extracted_df = pd.DataFrame(person_extracted, columns=["person_extracted"])
    #person_extracted_df.to_csv('person_extracted.csv', index=False)

    # MONEY Matching
    money_matcher = PhraseMatcher(nlp.vocab, attr="SHAPE")
    
    money_patterns = [nlp("$999.999.999.999.999"), nlp("$99.999.999.999.999"), nlp("$9.999.999.999.999"), 
                  nlp("$999.999.999.999"), nlp("$99.999.999.999"), nlp("$9.999.999.999"),
                  nlp("$999.999.999"), nlp("$99.999.999"), nlp("$9.999.999"), nlp("$999.999"), 
                  nlp("$99.999"),nlp("$9.999"),nlp("$999"),nlp("$99"),nlp("$9"),
                  
                  nlp("$999,999,999,999,999"), nlp("$99,999,999,999,999"), nlp("$9,999,999,999,999"), 
                  nlp("$999,999,999,999"), nlp("$99,999,999,999"), nlp("$9,999,999,999"),
                  nlp("$999,999,999"), nlp("$99,999,999"), nlp("$9,999,999"), nlp("$999,999"), 
                  nlp("$99,999"),nlp("$9,999"),
                  
                  nlp("$999.999.999.999.999,00"), nlp("$99.999.999.999.999,00"), nlp("$9.999.999.999.999,00"), 
                  nlp("$999.999.999.999,00"), nlp("$99.999.999.999,00"), nlp("$9.999.999.999,00"),
                  nlp("$999.999.999,00"), nlp("$99.999.999,00"), nlp("$9.999.999,00"), nlp("$999.999,00"), 
                  nlp("$99.999,00"),nlp("$9.999,00"),nlp("$999,00"),nlp("$99,00"),nlp("$9,00"),
                  
                  nlp("$999.999.999.999.999,0"), nlp("$99.999.999.999.999,0"), nlp("$9.999.999.999.999,0"), 
                  nlp("$999.999.999.999,0"), nlp("$99.999.999.999,0"), nlp("$9.999.999.999,0"),
                  nlp("$999.999.999,0"), nlp("$99.999.999,0"), nlp("$9.999.999,0"), nlp("$999.999,0"), 
                  nlp("$99.999,0"),nlp("$9.999,0"),nlp("$999,0"),nlp("$99,0"),nlp("$9,0"),
                  
                  nlp("$999.999.999.999.999.00"), nlp("$99.999.999.999.999.00"), nlp("$9.999.999.999.999.00"), 
                  nlp("$999.999.999.999.00"), nlp("$99.999.999.999.00"), nlp("$9.999.999.999.00"),
                  nlp("$999.999.999.00"), nlp("$99.999.999.00"), nlp("$9.999.999.00"), nlp("$999.999.00"), 
                  nlp("$99.999.00"),nlp("$9.999.00"),nlp("$999.00"),nlp("$99.00"),nlp("$9.00"),
                  
                  nlp("$999,999,999,999,999.00"), nlp("$99,999,999,999,999.00"), nlp("$9,999,999,999,999.00"), 
                  nlp("$999,999,999,999.00"), nlp("$99,999,999,999.00"), nlp("$9,999,999,999.00"),
                  nlp("$999,999,999.00"), nlp("$99,999,999.00"), nlp("$9,999,999.00"), nlp("$999,999.00"), 
                  nlp("$99,999.00"),nlp("$9,999.00"),
                  
                  nlp("$ 999.999.999.999.999.00"), nlp("$ 99.999.999.999.999.00"), nlp("$ 9.999.999.999.999.00"), 
                  nlp("$ 999.999.999.999.00"), nlp("$ 99.999.999.999.00"), nlp("$ 9.999.999.999.00"),
                  nlp("$ 999.999.999.00"), nlp("$ 99.999.999.00"), nlp("$ 9.999.999.00"), nlp("$ 999.999.00"), 
                  nlp("$ 99.999.00"),nlp("$ 9.999.00"),nlp("$ 999.00"),nlp("$ 99.00"),nlp("$ 9.00"),
                  
                  nlp("$ 999.999.999.999.999,00"), nlp("$ 99.999.999.999.999,00"), nlp("$ 9.999.999.999.999,00"), 
                  nlp("$ 999.999.999.999,00"), nlp("$ 99.999.999.999,00"), nlp("$ 9.999.999.999,00"),
                  nlp("$ 999.999.999,00"), nlp("$ 99.999.999,00"), nlp("$ 9.999.999,00"), nlp("$ 999.999,00"), 
                  nlp("$ 99.999,00"),nlp("$ 9.999,00"),nlp("$ 999,00"),nlp("$ 99,00"),nlp("$ 9,00"),
                  
                  nlp("$999,999,999,999,999,00"), nlp("$99,999,999,999,999,00"), nlp("$9,999,999,999,999,00"), 
                  nlp("$999,999,999,999,00"), nlp("$99,999,999,999,00"), nlp("$9,999,999,999,00"),
                  nlp("$999,999,999,00"), nlp("$99,999,999,00"), nlp("$9,999,999,00"), nlp("$999,999,00"), 
                  nlp("$99,999,00"),nlp("$9,999,00"),
                  
                  nlp("$ 999.999.999.999.999"), nlp("$ 99.999.999.999.999"), nlp("$ 9.999.999.999.999"), 
                  nlp("$ 999.999.999.999"), nlp("$ 99.999.999.999"), nlp("$ 9.999.999.999"),
                  nlp("$ 999.999.999"), nlp("$ 99.999.999"), nlp("$ 9.999.999"), nlp("$ 999.999"), 
                  nlp("$ 99.999"),nlp("$ 9.999"),nlp("$ 999"),nlp("$ 99"),nlp("$ 9"),
                  
                  nlp("$999999999999999.00"), nlp("$99999999999999.00"), nlp("$9999999999999.00"), 
                  nlp("$999999999999.00"), nlp("$99999999999.00"), nlp("$9999999999.00"),
                  nlp("$999999999.00"), nlp("$99999999.00"), nlp("$9999999.00"), nlp("$999999.00"), 
                  nlp("$99999.00"),nlp("$9999.00"),
                  nlp("$999999999999999,00"), nlp("$99999999999999,00"), nlp("$9999999999999,00"), 
                  nlp("$999999999999,00"), nlp("$99999999999,00"), nlp("$9999999999,00"),
                  nlp("$999999999,00"), nlp("$99999999,00"), nlp("$9999999,00"), nlp("$999999,00"), 
                  nlp("$99999,00"),nlp("$9999,00"),
                  nlp("$ 999999999999999.00"), nlp("$ 99999999999999.00"), nlp("$ 9999999999999.00"), 
                  nlp("$ 999999999999.00"), nlp("$ 99999999999.00"), nlp("$ 9999999999.00"),
                  nlp("$ 999999999.00"), nlp("$ 99999999.00"), nlp("$ 9999999.00"), nlp("$ 999999.00"), 
                  nlp("$ 99999.00"),nlp("$ 9999.00"),
                  nlp("$ 999999999999999,00"), nlp("$ 99999999999999,00"), nlp("$ 9999999999999,00"), 
                  nlp("$ 999999999999,00"), nlp("$ 99999999999,00"), nlp("$ 9999999999,00"),
                  nlp("$ 999999999,00"), nlp("$ 99999999,00"), nlp("$ 9999999,00"), nlp("$ 999999,00"), 
                  nlp("$ 99999,00"),nlp("$ 9999,00"),
                  nlp("$ 999999999999999"), nlp("$ 99999999999999"), nlp("$ 9999999999999"), 
                  nlp("$ 999999999999"), nlp("$ 99999999999"), nlp("$ 9999999999"),
                  nlp("$ 999999999"), nlp("$ 99999999"), nlp("$ 9999999"), nlp("$ 999999"), 
                  nlp("$ 99999"),nlp("$ 9999"),
                  
                  nlp("(914.000.000) m/cte"),nlp("$d,ddd,ddd,ddd.dd"),nlp("$ddd,ddd,ddd.dd"),
                  nlp("$dd,ddd,ddd.dd"),nlp("$d,ddd,ddd.dd"),nlp("$ddd,ddd.dd"),nlp("$ddd,ddd,ddd")
                  ]
    
    money_matcher.add('MONEY', None, *money_patterns)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component", "name_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in money_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="MONEY")

        # Overwrite the doc.ents and add the span
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "MONEY"])
    
    # Define the custom component
    def money_component(doc):
        # Apply the matcher to the doc
        matches = money_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="MONEY") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(money_component, after="name_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    money_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "MONEY"]
    money_extracted = []
    for i in range(len(money_list)):
        money_ent = money_list[i][0]
        money_extracted.append(money_ent)
    
    money_extracted_df = pd.DataFrame(money_extracted, columns=["money_extracted"])
    #money_extracted_df.to_csv('money_extracted.csv', index=False)
    
    # ENTITY RULER
    from spacy.pipeline import EntityRuler
    
    # ENTITY Matching
    ruler = EntityRuler(nlp).from_disk("patterns2.jsonl")
    
    nlp.add_pipe(ruler, after="money_component")
    #print(nlp.pipe_names)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component", "name_component", "money_component"):
        doc = nlp(text)

    # Print the entities in the document
    #print([(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents])
    
    #displacy.render(doc, style="ent")
    
    org_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ORG"]
    org_extracted = []
    for i in range(len(org_list)):
        org_ent = org_list[i][0]
        org_extracted.append(org_ent)
    
    org_extracted_df = pd.DataFrame(org_extracted, columns=["org_extracted"])
    #org_extracted_df.to_csv('org_extracted.csv', index=False)
    
    # VISUALIZING IDENTIFIED ENTITIES
    doc = nlp(text)
    
    displacy.render(doc, style='ent', jupyter=True)   
    html =  displacy.render(doc, style='ent', jupyter=False, page=True)
    
    def upload_html(html_string,bucket,key,aws_access_key_id,aws_secret_access_key):
        '''
            Upload data to storage S3, aws_acces_key_id and aws_secret_access_key are provided by AWS.
            This function is only if you require save the information in SW. 
        '''

        client = boto3.client('s3',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)
        
        obj = client.put_object(Bucket=bucket, 
                                Key=key2, 
                                Body=html_string, 
                                CacheControl="max-age=0,no-cache,no-store,must-revalidate",
                                ContentType="text/html",
                                ACL="public-read")
        return obj
    
    # LOADING HTML TO S3 BUCKET    
    upload_html(html,bucket,key2,aws_access_key_id,aws_secret_access_key)      
    
    # VALIDATION OF IDENTIFIED ENTITIES
    # Date Validation
    
    import dateparser
    from dateparser.search import search_dates
    #import datetime
    import locale
    locale.setlocale(locale.LC_TIME, "es")
    ddp = dateparser.DateDataParser(languages=['es'])
    
    # Function to calculate similarity
    from difflib import SequenceMatcher
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('del', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('de', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dias', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('mes', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('(', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace(')', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diez', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('once', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('doce', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('trece', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('catorce', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('quince', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dieciseis', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diecisiete', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dieciocho', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diecinueve', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('uno', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dos', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('tres', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('cuatro', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('cinco', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('seis', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('siete', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('ocho', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('nueve', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('mil', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('.', "")
    #date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.lstrip('0')
    date_extracted_df['date_extracted']
    
    extracted_dates_list = date_extracted_df['date_extracted'].apply(lambda x: dateparser.parse(x))
    #extracted_dates_list
    
    extracted_dates_list=extracted_dates_list.apply(lambda x: x.date())
    extracted_dates_list
    
    extracted_dates_set = set(extracted_dates_list)
    extracted_dates_set 
    
    date_to_validate=df.iloc[:,4].to_numpy()[0]
    date_to_validate

    
    # Validating date
    date_validated = 0
    dates_similarity = 0.0
    date_doc=str(object='')

    for fecha in extracted_dates_set:
        date_similarity = round(similar(str(fecha),str(date_to_validate)),2)
        if date_similarity > dates_similarity:
                dates_similarity = date_similarity
                date_doc=fecha
                
    #print(dates_similarity)

    if dates_similarity >= 0.9:
        date_validated = 1
        print(f'DATE {date_to_validate} is VALIDATED')
    else:
        print(f'DATE {date_to_validate} is NOT VALIDATED')
        
        
    # ID Validation

    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('.', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace(',', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace(':', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('-', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('no', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('n°', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('  ', " ")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('   ', " ")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('numero', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('no.', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('cc', "cedula de ciudadania")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('doc', "cedula de ciudadania")
    #id_extracted_df['id_extracted']     
    
    id_extracted_list=id_extracted_df['id_extracted'].unique()
    id_extracted_list=id_extracted_list.tolist()
    id_extracted_list
    
    id_type_to_validate=df.iloc[:,1].to_numpy()[0]
    #id_type_to_validate
    
    id_number_to_validate=df.iloc[:,2].to_numpy()[0]
    #id_number_to_validate
    
    id_number_to_validate=id_number_to_validate.replace('.', "")
    id_number_to_validate=id_number_to_validate.replace('-', "")
    
    id_to_validate = id_type_to_validate + ' ' + id_number_to_validate
    id_to_validate
    
    # Validating ID
    id_validated = 0
    ids_similarity = 0.0
    id_doc=str(object='')

    for id in id_extracted_list:
        id_similarity = round(similar(str(id),str(id_to_validate)),2)
        if id_similarity > ids_similarity:
                ids_similarity = id_similarity
                id_doc=id 
    
    ids_similarity
    
    if ids_similarity >= 0.9:
        id_validated = 1
        print(f'ID {id_to_validate} is VALIDATED')
    else:
        #ids_doc = ' '.join(word for word in no_id_doc.split()[0:1])
        print(f'ID {id_to_validate} is NOT VALIDATED')
        
    docs_list=id_doc.split()
    #docs_list    
    
    doc_type = []
    doc_number = []
    for item in docs_list:
        if item.isdecimal():
            doc_number.append(item)
        else:
            doc_type.append(item)
            
    doc_type= ' '.join(word for word in doc_type)
    doc_number= ' '.join(word for word in doc_number)    
    
    id_type_similarity = round(similar(str(doc_type),str(id_type_to_validate)),2)
    id_number_similarity = round(similar(str(doc_number),str(id_number_to_validate)),2)
    
    
    # NAME Validation
    
    person_extracted_list=person_extracted_df['person_extracted'].unique()
    person_extracted_list=person_extracted_list.tolist()
    person_extracted_list
    
    name_to_validate=df.iloc[:,3].to_numpy()[0]
    name_to_validate
    
    name_to_validate_list = name_to_validate.split()
    name_to_validate_list
    
    # Validating name
    name_validated = 0
    nombres = []
    no_nombres = []
    for nombre in name_to_validate_list:
        for persona in person_extracted_list:
            if nombre == persona:
                nombres.append(nombre)
            else:
                no_nombres.append(persona)
    
    name_doc = ' '.join(word for word in nombres)
    name_doc
    
    no_name_doc = ' '.join(word for word in no_nombres)
    no_name_doc
    
    name_similarity = round(similar(name_doc,name_to_validate),2)
    name_similarity
    
    if name_similarity >= 0.8:
        name_validated = 1
        nombre_doc = name_doc
        print(f'PERSON {name_to_validate} is VALIDATED')
    else:
        nombre_doc = ' '.join(word for word in no_name_doc.split()[0:4])
        print(f'PERSON {name_to_validate} is NOT VALIDATED')
        
    # MONEY Validation

    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace('$', "")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace("  ", " ")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace("   ", " ")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.lstrip()
    money_extracted_df['money_extracted']
        
    def money_format(money_figure):
    
        money_extracted_list = money_figure.split('.')
        #print(money_extracted_list) 
        element_list=[]
        for element in money_extracted_list:
            sublist=element.split(',')
            element_list.append(sublist)

        flat_element_list = [item for sublist in element_list for item in sublist]
        #print(flat_element_list)
        
        if (len(flat_element_list[-1])==1) | (len(flat_element_list[-1])==2):
            quantity=' '.join(number for number in flat_element_list[:-1])
            #print(f'm {quantity}')
            quantity=quantity.replace(" ", "")
            #print(f'n {quantity}')
            quantity=quantity+'.'+ flat_element_list[-1]
            #print(f'o {quantity}')
            quantity="${:,.2f}".format(float(quantity))
            #print(f'p {quantity}') 

        else:
            quantity=' '.join(number for number in flat_element_list)
            #print(f'A {quantity}')
            quantity=quantity.replace(" ", "")
            #print(f'B {quantity}')
            quantity=quantity+'.00'
            #print(f'C {quantity}')
            quantity="${:,.2f}".format(float(quantity))
            #print(f'D {quantity}')
        
        return quantity
    
    money_extracted_list=money_extracted_df['money_extracted'].apply(lambda x: money_format(x))
    money_extracted_list
    
    money_extracted_set = set(money_extracted_list)
    money_extracted_set
    
    money_to_validate=df.iloc[:,5].to_numpy()[0]
    money_to_validate
    
    money_add_to_validate=df.iloc[:,6].to_numpy()[0]
    money_add_to_validate
    
    #round(money_to_validate,2)
    money_to_validate="${:,.2f}".format(money_to_validate)
    money_to_validate
    
    #round(money_add_to_validate,2)
    money_add_to_validate="${:,.2f}".format(money_add_to_validate)
    money_add_to_validate
    
    # Validating MONEY
    money_validated = 0
    moneys_similarity = 0.0
    money_doc=str(object='')

    for figure in money_extracted_set:
        money_similarity = round(similar(str(figure),str(money_to_validate)),2)
        if money_similarity > moneys_similarity:
                moneys_similarity = money_similarity
                money_doc=figure
                            
    # Validating MONEY ADD
    money_add_validated = 0
    moneys_add_similarity = 0.0
    money_add_doc=str(object='')

    for figure in money_extracted_set:
        money_add_similarity = round(similar(str(figure),str(money_add_to_validate)),2)
        if money_add_similarity > moneys_add_similarity:
                moneys_add_similarity = money_add_similarity
                money_add_doc=figure
                
    moneys_similarity
    
    moneys_add_similarity
    
    if moneys_similarity >= 0.9:
        money_validated = 1
        print(f'MONEY {money_to_validate} is VALIDATED')
    else:
        print(f'MONEY {money_to_validate} is NOT VALIDATED')
    
    
    if moneys_add_similarity >= 0.9:
        money_add_validated = 1
        print(f'MONEY ADD {money_add_to_validate} is VALIDATED')
    else:
        print(f'MONEY ADD {money_add_to_validate} is NOT VALIDATED')
        
    # ORGANIZATION Validation

    org_extracted_list=org_extracted_df['org_extracted'].unique()
    org_extracted_list=org_extracted_list.tolist()
    org_extracted_list
    
    org_extracted_list=org_extracted_df['org_extracted'].apply(lambda x: x.split())
    flat_org_extracted_list = [item for sublist in org_extracted_list for item in sublist]
    org_extracted_set = set(flat_org_extracted_list)
    org_extracted_set
    
    org_to_validate=df.iloc[:,7].to_numpy()[0]
    org_to_validate
    
    org_to_validate=org_to_validate.replace('-', "")
    org_to_validate
    
    org_to_validate_list = org_to_validate.split()
    org_to_validate_list
    
    # Validating organization
    org_validated = 0
    orgs = []
    no_orgs = []
    for entidad in org_to_validate_list:
        for org in org_extracted_set:
            if entidad == org:
                orgs.append(entidad)
            else:
                no_orgs.append(org)    

    org_doc = ' '.join(word for word in orgs)
    org_doc  

    no_org_doc = ' '.join(word for word in no_orgs)
    no_org_doc    
    
    org_similarity = round(similar(org_doc,org_to_validate),2)
    org_similarity
    
    if org_similarity >= 0.8:
        org_validated = 1
        orga_doc = org_doc
        print(f'ORGANIZATION {org_to_validate} is VALIDATED')
    else:
        orga_doc = ' '.join(word for word in no_org_doc.split()[0:4])
        print(f'ORGANIZATION {org_to_validate} is NOT VALIDATED')
    
    #Calculating Validation Score
    
    number_of_variables = 7
    validation_score = (org_similarity + 
                    moneys_similarity + 
                    moneys_add_similarity +
                    id_type_similarity + 
                    id_number_similarity +
                    name_similarity + 
                    dates_similarity)/ number_of_variables

    if validation_score >= 0.9:
        contract_validation_status = 'GREEN'
    elif validation_score > 0.6:
        contract_validation_status = 'YELLOW'
    else:
        contract_validation_status = 'RED'

    print('VALIDATION REPORT')
    print('---------------------------------------------')
    print(f'Validation score is:     {round(validation_score,2)}, contract validation status is:   {contract_validation_status}.')
    print('')
    print('Entity,                   ( Database,        Document,        Similarity)')
    print(f'Date similarity is:      {date_to_validate, date_doc, dates_similarity}')
    print(f'Name similarity is:      {name_to_validate, nombre_doc, name_similarity}')
    print(f'Id type similarity is:   {id_type_to_validate, doc_type, id_type_similarity}')
    print(f'Id number similarity is: {id_number_to_validate, doc_number, id_number_similarity}')
    print(f'Money similarity is:     {money_to_validate, money_doc, moneys_similarity}')
    print(f'Money add similarity is: {money_add_to_validate, money_add_doc, moneys_add_similarity}')
    print(f'Entity similarity is:    {org_to_validate, orga_doc, org_similarity}')
    print('---------------------------------------------')
    print('')
    
    import psycopg2 as ps
    
    host = 'ds4a-demo-instance.cwmtqeffz1wh.us-east-2.rds.amazonaws.com'
    port = 5432
    user = 'team_34_user'
    password = 'team34'
    database = 'project_team_34_db'
    
    try:
        connection = ps.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)
        cursor = connection.cursor()

        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 7, date_to_validate, date_doc, dates_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 4, name_to_validate, nombre_doc, name_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 5, id_type_to_validate, doc_type, id_type_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 6, id_number_to_validate, doc_number, id_number_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 9, money_to_validate, money_doc, moneys_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 10, money_add_to_validate, money_add_doc, moneys_add_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 1, org_to_validate, orga_doc, org_similarity))

        cursor.execute("UPDATE doc_contrato SET procesado = %s WHERE uuid = %s", (1, uid))

        connection.commit()
        count = cursor.rowcount
        print (count, "Record inserted successfully into doc_validados table")

    except (Exception, ps.Error) as error :
        if(connection):
            print("Failed to insert record into mobile table", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        
        
    return validation_score
   


def NER_contrato_textract(df, contract_path):
    #Function that performs 

    import pandas as pd
    import logging
    from io import StringIO 
    import os
    
    import boto3
    from botocore.exceptions import ClientError
    import time
    
    ## Bucket de Alexis
    aws_access_key_id="AKIAZ7JA337WYTRP5TVZ"
    aws_secret_access_key="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"
    region_name = "us-east-2"
    bucket = "bootcampaws315"
    
    uid = contract_path.split("/")[0]
    document_name = contract_path.split("/")[1][:-4]
    key=uid + '/' + document_name + '.csv'
    key2=uid + '/' + document_name + '.html'
    
    print(f'Working on UUID:   {uid}')
    print(f'Working on document:   {contract_path}')
    
    # Function to extract data from Amazon Textract

    def startJob(s3BucketName, objectName):
        response = None
        client = boto3.client('textract')
        response = client.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': s3BucketName,
                'Name': objectName
            }
        })

        return response["JobId"]

    def isJobComplete(jobId):
        time.sleep(5)
        client = boto3.client('textract')
        response = client.get_document_text_detection(JobId=jobId)
        status = response["JobStatus"]
        print("Job status: {}".format(status))

        while(status == "IN_PROGRESS"):
            time.sleep(5)
            response = client.get_document_text_detection(JobId=jobId)
            status = response["JobStatus"]
            print("Job status: {}".format(status))

        return status

    def getJobResults(jobId):

        pages = []

        time.sleep(5)

        client = boto3.client('textract')
        response = client.get_document_text_detection(JobId=jobId)
        
        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

        while(nextToken):
            time.sleep(5)

            response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)

            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if('NextToken' in response):
                nextToken = response['NextToken']

        return pages
        
    # Uploading file in S3 Bucket
    s3BucketName = bucket
    documentName = contract_path

    jobId = startJob(s3BucketName, documentName)
    print("Started job with id: {}".format(jobId))
    if(isJobComplete(jobId)):
        response = getJobResults(jobId)

    #print(response)

    # Print text
    print("\nText\n========")
    text = ""

    # Print detected text
    for resultPage in response:
        for item in resultPage["Blocks"]:
            if item["BlockType"] == "LINE":
                #print ('\033[94m' +  item["Text"] + '\033[0m')
                text = text + " " + item["Text"]     
                
    
    # Saving Text File in bucket
    data = pd.DataFrame([text],columns=['text'])
    
    def upload_data(data,bucket,key,aws_access_key_id,aws_secret_access_key):
        '''
            Upload data to storage S3, aws_acces_key_id and aws_secret_access_key are provided by AWS.
            This function is only if you require save the information in SW. 
        '''

        client = boto3.client('s3',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)
        csv_buffer = StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        obj = client.put_object(Bucket=bucket, 
                                Key=key, 
                                Body=csv_buffer.getvalue(), 
                                ACL='public-read')

        return obj

    upload_data(data,bucket,key,aws_access_key_id,aws_secret_access_key)    
    
    # NER FUNCTION

    import es_core_news_sm # Spanish model small
    nlp = es_core_news_sm.load()
    
    import re
    from unicodedata import normalize

    def formatingText(text):
        text = text.lower()
        text = re.sub('<.*?>', '', text)
        #text = re.sub(':.*?:', '', text)
        text = re.sub(r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", normalize( "NFD", text), 0, re.I)
        #text = normalize( 'NFC', text)
        #text = re.sub('[^a-z ]', '', text)
        return text
    
    text=formatingText(text)
    
    # spaCy
    doc = nlp(text)
    
    # Customized sentence splitting
    nlp = es_core_news_sm.load()
    boundary = re.compile('^[0-9]$')
    numero = re.compile(r'No')

    def custom_seg(doc):
        prev = doc[0].text
        length = len(doc)
        for index, token in enumerate(doc):
            if (token.text == '.' and boundary.match(prev) and index!=(length - 1)):
                doc[index+1].sent_start = False
            if (token.text == '.' and numero.match(prev) and index!=(length - 1)):
                doc[index+1].sent_start = False    
            prev = token.text
        return doc

    nlp.add_pipe(custom_seg, before='parser')

    #sbd = nlp.create_pipe('sentencizer')
    #nlp.add_pipe(sbd)

    doc = nlp(text)
    
    # Creating list of strings
    sent_list=[sentence.string.strip() for sentence in doc.sents]
    
    # Creating dataframe of sentences
    sent_df = pd.DataFrame({'sentences':sent_list})
    #print (sent_df)
    
    # Token Matcher
    from spacy.matcher import Matcher
    
    # DATE Matcher
    # Matcher Function
    def create_date_patterns():
        date_patterns = [ 
        [{'TEXT': {'REGEX': '(0[1-9]|[12]\d|3[01])\/(0[1-9]|1[0-2])\/([12]\d{3})'}}],
        [{'TEXT': {'REGEX': '([1-9]|0[1-9]|[12]\d|3[01])\/(0[1-9]|1[0-2])\/([1-9]\d{1})'}}],
        
        [{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"POS":"NUM"},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"POS":"NUM"},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"POS":"NUM"},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"POS":"NUM"},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"LOWER":"de"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}},{"SHAPE":"dddd"}],
        [{"POS":"NUM"},{"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}},{"SHAPE":"dddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"TEXT":{"IN": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]}}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"}, {"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"d.ddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"SHAPE":"d.ddd"}],
        
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"}, {"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"LOWER":"dos"}, {"LOWER":"mil"}, {"POS":"NUM"}, {"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"del"}, {"LOWER":"mes"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"},{"LOWER":"("}, {"SHAPE":"dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"de"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"LOWER":"del"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"POS":"NUM"}, {"LOWER":")"}, {"LOWER":"dias"},{"LOWER":"de"}, {"POS":"INTJ"}, {"SHAPE":"dddd"}],
        [{"LOWER":"("}, {"SHAPE":"dd.dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dd.dd.dddd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dddd-dd-dd"}, {"LOWER":")"}],
        [{"LOWER":"("}, {"SHAPE":"dd-dd-dddd"}, {"LOWER":")"}],
        [{"SHAPE":"dddd-dd-dd"}],
        [{"SHAPE":"dd-dd-dddd"}]
        ]  
        
        return date_patterns
    
    date_matcher = Matcher(nlp.vocab)
    date_matcher.add("DATE", None, *create_date_patterns())
    
    doc = nlp(text)
    doc.ents = []
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in date_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="DATE")

        # Overwrite the doc.ents and add the span
        #doc.ents = [span]
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "DATE"])
    
    # Define the custom component
    def date_component(doc):
        # Apply the matcher to the doc
        matches = date_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="DATE") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    nlp.add_pipe(date_component, after="ner")
    #print(nlp.pipe_names)
    
    from spacy import displacy
    #displacy.render(doc, style="ent")  
    
    nlp.remove_pipe('ner')
    
    date_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "DATE"]
    date_extracted = []
    for i in range(len(date_list)):
        date_ent = date_list[i][0]
        date_extracted.append(date_ent)
    
    date_extracted_df = pd.DataFrame(date_extracted, columns=["date_extracted"])
    #date_extracted_df.to_csv('date_extracted.csv', index=False)

    # ID Matcher
    # Matcher Function
    def create_id_patterns():
        id_patterns = [ 
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"es"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no"}, {"IS_PUNCT":True, "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"},{"LOWER":"numero"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"dddd-d"}],
        [{"LOWER":"nit"}, {"IS_PUNCT":True, "OP": "?"},{"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"SHAPE":"ddd.ddd.ddd-d"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"no"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"n"}, {"LOWER":"°"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"n"}, {"LOWER":"°"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"nro"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"no", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NOUN"}],
        [ {"LOWER":"numero"}, {"LOWER":"de"}, {"LOWER":"cedula"},  {"LOWER":"no", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"n°"},{"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cc"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"c.c."}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"LOWER":"c.c.no"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"SHAPE":"x.xd.ddd.ddd"}],
        [{"SHAPE":"x.xdd.ddd.ddd"}],
        [{"SHAPE":"x.xddd.ddd.ddd"}],
        [{"SHAPE":"x.xd.ddd.ddd.ddd"}],
        [{"SHAPE":"x.x.d.ddd.ddd"}],
        [{"SHAPE":"x.x.dd.ddd.ddd"}],
        [{"SHAPE":"x.x.ddd.ddd.ddd"}],
        [{"SHAPE":"x.x.d.ddd.ddd.ddd"}],
        
        [{"LOWER":"doc"},  {"IS_PUNCT":True, "OP": "?"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        [{"LOWER":"c.c"}, {"LOWER":"no", "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NOUN"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"n°"}, {"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"},{"POS":"NUM"}],
        
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"n°", "OP": "?"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"numero"},{"IS_PUNCT":True, "OP": "?"}, {"IS_PUNCT":True, "OP": "?"}, {"POS":"NUM"}],
        [{"LOWER":"cedula"}, {"LOWER":"de"}, {"LOWER":"ciudadania"}, {"LOWER":"numero"},{"SHAPE":"dd.ddd.ddd"}],
        [{"LOWER":"cedula"}, {"LOWER":":",  "OP": "?"}, {"LOWER":"n°"},{"SHAPE":"dd.ddd.ddd"}]
        ]
    
        return id_patterns

    id_matcher = Matcher(nlp.vocab)
    id_matcher.add("ID", None, *create_id_patterns())
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in id_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="ID_NUMBER")

        # Overwrite the doc.ents and add the span
        #doc.ents = [span]
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ID_NUMBER"])
    
    # Define the custom component
    def id_component(doc):
        # Apply the matcher to the doc
        matches = id_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="ID_NUMBER") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(id_component, after="date_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    id_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ID_NUMBER"]
    id_extracted = []
    for i in range(len(id_list)):
        id_ent = id_list[i][0]
        id_extracted.append(id_ent)
    
    id_extracted_df = pd.DataFrame(id_extracted, columns=["id_extracted"])
    #id_extracted_df.to_csv('id_extracted.csv', index=False)

    # PHRASE MATCHER
    from spacy.matcher import PhraseMatcher
    
    # NAME Matcher
    name_matcher = PhraseMatcher(nlp.vocab)
    
    nombres = pd.read_csv('lista_nombres_refiltrados_simple.csv')
    nombre_list=nombres['nombres']
    nombre_patterns = list(nlp.pipe(nombre_list.values))
    
    name_matcher.add("PERSON", None, *nombre_patterns)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in name_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="PERSON")

        # Overwrite the doc.ents and add the span
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "PERSON"])
    
    # Define the custom component REMOVING OVERLAPPED SPANS
    def name_component(doc):
        # Apply the matcher to the doc
        matches = name_matcher(doc)
        
        new_entities = []
        seen_tokens = set()
        entities = doc.ents
        
        for match_id, start, end in matches:
            # check for end - 1 here because boundaries are inclusive
            if start not in seen_tokens and end - 1 not in seen_tokens:
                new_entities.append(Span(doc, start, end, label=match_id))
                entities = [
                    e for e in entities if not (e.start < end and e.end > start)
                ]
                seen_tokens.update(range(start, end))
        
        doc.ents = tuple(entities) + tuple(new_entities) 
            
        # Create a Span for each match and assign the label "PERSON"
        #spans = [Span(doc, start, end, label="PERSON") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        #doc.ents = list(doc.ents) + spans
        
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(name_component, after="id_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    person_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "PERSON"]
    person_extracted = []
    for i in range(len(person_list)):
        person_ent = person_list[i][0]
        person_extracted.append(person_ent)
    
    person_extracted_df = pd.DataFrame(person_extracted, columns=["person_extracted"])
    #person_extracted_df.to_csv('person_extracted.csv', index=False)

    # MONEY Matching
    money_matcher = PhraseMatcher(nlp.vocab, attr="SHAPE")
    
    money_patterns = [nlp("$999.999.999.999.999"), nlp("$99.999.999.999.999"), nlp("$9.999.999.999.999"), 
                  nlp("$999.999.999.999"), nlp("$99.999.999.999"), nlp("$9.999.999.999"),
                  nlp("$999.999.999"), nlp("$99.999.999"), nlp("$9.999.999"), nlp("$999.999"), 
                  nlp("$99.999"),nlp("$9.999"),nlp("$999"),nlp("$99"),nlp("$9"),
                  
                  nlp("$999,999,999,999,999"), nlp("$99,999,999,999,999"), nlp("$9,999,999,999,999"), 
                  nlp("$999,999,999,999"), nlp("$99,999,999,999"), nlp("$9,999,999,999"),
                  nlp("$999,999,999"), nlp("$99,999,999"), nlp("$9,999,999"), nlp("$999,999"), 
                  nlp("$99,999"),nlp("$9,999"),
                  
                  nlp("$999.999.999.999.999,00"), nlp("$99.999.999.999.999,00"), nlp("$9.999.999.999.999,00"), 
                  nlp("$999.999.999.999,00"), nlp("$99.999.999.999,00"), nlp("$9.999.999.999,00"),
                  nlp("$999.999.999,00"), nlp("$99.999.999,00"), nlp("$9.999.999,00"), nlp("$999.999,00"), 
                  nlp("$99.999,00"),nlp("$9.999,00"),nlp("$999,00"),nlp("$99,00"),nlp("$9,00"),
                  
                  nlp("$999.999.999.999.999,0"), nlp("$99.999.999.999.999,0"), nlp("$9.999.999.999.999,0"), 
                  nlp("$999.999.999.999,0"), nlp("$99.999.999.999,0"), nlp("$9.999.999.999,0"),
                  nlp("$999.999.999,0"), nlp("$99.999.999,0"), nlp("$9.999.999,0"), nlp("$999.999,0"), 
                  nlp("$99.999,0"),nlp("$9.999,0"),nlp("$999,0"),nlp("$99,0"),nlp("$9,0"),
                  
                  nlp("$999.999.999.999.999.00"), nlp("$99.999.999.999.999.00"), nlp("$9.999.999.999.999.00"), 
                  nlp("$999.999.999.999.00"), nlp("$99.999.999.999.00"), nlp("$9.999.999.999.00"),
                  nlp("$999.999.999.00"), nlp("$99.999.999.00"), nlp("$9.999.999.00"), nlp("$999.999.00"), 
                  nlp("$99.999.00"),nlp("$9.999.00"),nlp("$999.00"),nlp("$99.00"),nlp("$9.00"),
                  
                  nlp("$999,999,999,999,999.00"), nlp("$99,999,999,999,999.00"), nlp("$9,999,999,999,999.00"), 
                  nlp("$999,999,999,999.00"), nlp("$99,999,999,999.00"), nlp("$9,999,999,999.00"),
                  nlp("$999,999,999.00"), nlp("$99,999,999.00"), nlp("$9,999,999.00"), nlp("$999,999.00"), 
                  nlp("$99,999.00"),nlp("$9,999.00"),
                  
                  nlp("$ 999.999.999.999.999.00"), nlp("$ 99.999.999.999.999.00"), nlp("$ 9.999.999.999.999.00"), 
                  nlp("$ 999.999.999.999.00"), nlp("$ 99.999.999.999.00"), nlp("$ 9.999.999.999.00"),
                  nlp("$ 999.999.999.00"), nlp("$ 99.999.999.00"), nlp("$ 9.999.999.00"), nlp("$ 999.999.00"), 
                  nlp("$ 99.999.00"),nlp("$ 9.999.00"),nlp("$ 999.00"),nlp("$ 99.00"),nlp("$ 9.00"),
                  
                  nlp("$ 999.999.999.999.999,00"), nlp("$ 99.999.999.999.999,00"), nlp("$ 9.999.999.999.999,00"), 
                  nlp("$ 999.999.999.999,00"), nlp("$ 99.999.999.999,00"), nlp("$ 9.999.999.999,00"),
                  nlp("$ 999.999.999,00"), nlp("$ 99.999.999,00"), nlp("$ 9.999.999,00"), nlp("$ 999.999,00"), 
                  nlp("$ 99.999,00"),nlp("$ 9.999,00"),nlp("$ 999,00"),nlp("$ 99,00"),nlp("$ 9,00"),
                  
                  nlp("$999,999,999,999,999,00"), nlp("$99,999,999,999,999,00"), nlp("$9,999,999,999,999,00"), 
                  nlp("$999,999,999,999,00"), nlp("$99,999,999,999,00"), nlp("$9,999,999,999,00"),
                  nlp("$999,999,999,00"), nlp("$99,999,999,00"), nlp("$9,999,999,00"), nlp("$999,999,00"), 
                  nlp("$99,999,00"),nlp("$9,999,00"),
                  
                  nlp("$ 999.999.999.999.999"), nlp("$ 99.999.999.999.999"), nlp("$ 9.999.999.999.999"), 
                  nlp("$ 999.999.999.999"), nlp("$ 99.999.999.999"), nlp("$ 9.999.999.999"),
                  nlp("$ 999.999.999"), nlp("$ 99.999.999"), nlp("$ 9.999.999"), nlp("$ 999.999"), 
                  nlp("$ 99.999"),nlp("$ 9.999"),nlp("$ 999"),nlp("$ 99"),nlp("$ 9"),
                  
                  nlp("$999999999999999.00"), nlp("$99999999999999.00"), nlp("$9999999999999.00"), 
                  nlp("$999999999999.00"), nlp("$99999999999.00"), nlp("$9999999999.00"),
                  nlp("$999999999.00"), nlp("$99999999.00"), nlp("$9999999.00"), nlp("$999999.00"), 
                  nlp("$99999.00"),nlp("$9999.00"),
                  nlp("$999999999999999,00"), nlp("$99999999999999,00"), nlp("$9999999999999,00"), 
                  nlp("$999999999999,00"), nlp("$99999999999,00"), nlp("$9999999999,00"),
                  nlp("$999999999,00"), nlp("$99999999,00"), nlp("$9999999,00"), nlp("$999999,00"), 
                  nlp("$99999,00"),nlp("$9999,00"),
                  nlp("$ 999999999999999.00"), nlp("$ 99999999999999.00"), nlp("$ 9999999999999.00"), 
                  nlp("$ 999999999999.00"), nlp("$ 99999999999.00"), nlp("$ 9999999999.00"),
                  nlp("$ 999999999.00"), nlp("$ 99999999.00"), nlp("$ 9999999.00"), nlp("$ 999999.00"), 
                  nlp("$ 99999.00"),nlp("$ 9999.00"),
                  nlp("$ 999999999999999,00"), nlp("$ 99999999999999,00"), nlp("$ 9999999999999,00"), 
                  nlp("$ 999999999999,00"), nlp("$ 99999999999,00"), nlp("$ 9999999999,00"),
                  nlp("$ 999999999,00"), nlp("$ 99999999,00"), nlp("$ 9999999,00"), nlp("$ 999999,00"), 
                  nlp("$ 99999,00"),nlp("$ 9999,00"),
                  nlp("$ 999999999999999"), nlp("$ 99999999999999"), nlp("$ 9999999999999"), 
                  nlp("$ 999999999999"), nlp("$ 99999999999"), nlp("$ 9999999999"),
                  nlp("$ 999999999"), nlp("$ 99999999"), nlp("$ 9999999"), nlp("$ 999999"), 
                  nlp("$ 99999"),nlp("$ 9999"),
                  
                  nlp("(914.000.000) m/cte"),nlp("$d,ddd,ddd,ddd.dd"),nlp("$ddd,ddd,ddd.dd"),
                  nlp("$dd,ddd,ddd.dd"),nlp("$d,ddd,ddd.dd"),nlp("$ddd,ddd.dd"),nlp("$ddd,ddd,ddd")
                  ]
    
    money_matcher.add('MONEY', None, *money_patterns)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component", "name_component"):
        doc = nlp(text)
    
    # Iterate over the matches
    from spacy.tokens import Doc, Span
    for match_id, start, end in money_matcher(doc):
        # Create a Span with the label for "ID TIPO"
        span = Span(doc, start, end, label="MONEY")

        # Overwrite the doc.ents and add the span
        doc.ents = list(doc.ents) + [span]

        # Get the span's root head token
        span_root_head = span.root.head
        # Print the text of the span root's head token and the span text
        #print(span_root_head.text, "-->", span.text)

    # Print the entities in the document
    #print([(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "MONEY"])
    
    # Define the custom component
    def money_component(doc):
        # Apply the matcher to the doc
        matches = money_matcher(doc)
        # Create a Span for each match and assign the label "ANIMAL"
        spans = [Span(doc, start, end, label="MONEY") for match_id, start, end in matches]
        # Overwrite the doc.ents with the matched spans
        doc.ents = list(doc.ents) + spans
        return doc
    
    # Add the component to the pipeline after the "ner" component
    nlp.add_pipe(money_component, after="name_component")
    #print(nlp.pipe_names)
    
    #displacy.render(doc, style="ent")
    
    money_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "MONEY"]
    money_extracted = []
    for i in range(len(money_list)):
        money_ent = money_list[i][0]
        money_extracted.append(money_ent)
    
    money_extracted_df = pd.DataFrame(money_extracted, columns=["money_extracted"])
    #money_extracted_df.to_csv('money_extracted.csv', index=False)
    
    # ENTITY RULER
    from spacy.pipeline import EntityRuler
    
    # ENTITY Matching
    ruler = EntityRuler(nlp).from_disk("patterns2.jsonl")
    
    nlp.add_pipe(ruler, after="money_component")
    #print(nlp.pipe_names)
    
    # Create a doc and reset existing entities
    with nlp.disable_pipes("date_component", "id_component", "name_component", "money_component"):
        doc = nlp(text)

    # Print the entities in the document
    #print([(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents])
    
    #displacy.render(doc, style="ent")
    
    org_list=[(ent.text, ent.label_) for ent in doc.ents if ent.label_ == "ORG"]
    org_extracted = []
    for i in range(len(org_list)):
        org_ent = org_list[i][0]
        org_extracted.append(org_ent)
    
    org_extracted_df = pd.DataFrame(org_extracted, columns=["org_extracted"])
    #org_extracted_df.to_csv('org_extracted.csv', index=False)
    
    # VISUALIZING IDENTIFIED ENTITIES
    doc = nlp(text)
    
    displacy.render(doc, style='ent', jupyter=True)   
    html =  displacy.render(doc, style='ent', jupyter=False, page=True)
    
    def upload_html(html_string,bucket,key,aws_access_key_id,aws_secret_access_key):
        '''
            Upload data to storage S3, aws_acces_key_id and aws_secret_access_key are provided by AWS.
            This function is only if you require save the information in SW. 
        '''

        client = boto3.client('s3',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)
        
        obj = client.put_object(Bucket=bucket, 
                                Key=key2, 
                                Body=html_string, 
                                CacheControl="max-age=0,no-cache,no-store,must-revalidate",
                                ContentType="text/html",
                                ACL="public-read")
        return obj
    
    # LOADING HTML TO S3 BUCKET    
    upload_html(html,bucket,key2,aws_access_key_id,aws_secret_access_key)      
    
    # VALIDATION OF IDENTIFIED ENTITIES
    # Date Validation
    
    import dateparser
    from dateparser.search import search_dates
    #import datetime
    import locale
    locale.setlocale(locale.LC_TIME, "es")
    ddp = dateparser.DateDataParser(languages=['es'])
    
    # Function to calculate similarity
    from difflib import SequenceMatcher
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('del', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('de', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dias', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('mes', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('(', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace(')', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diez', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('once', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('doce', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('trece', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('catorce', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('quince', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dieciseis', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diecisiete', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dieciocho', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('diecinueve', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('uno', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('dos', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('tres', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('cuatro', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('cinco', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('seis', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('siete', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('ocho', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('nueve', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('mil', "")
    date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.replace('.', "")
    #date_extracted_df['date_extracted']=date_extracted_df['date_extracted'].str.lstrip('0')
    date_extracted_df['date_extracted']
    
    extracted_dates_list = date_extracted_df['date_extracted'].apply(lambda x: dateparser.parse(x))
    #extracted_dates_list
    
    extracted_dates_list=extracted_dates_list.apply(lambda x: x.date())
    extracted_dates_list
    
    extracted_dates_set = set(extracted_dates_list)
    extracted_dates_set 
    
    date_to_validate=df.iloc[:,4].to_numpy()[0]
    date_to_validate

    
    # Validating date
    date_validated = 0
    dates_similarity = 0.0
    date_doc=str(object='')

    for fecha in extracted_dates_set:
        date_similarity = round(similar(str(fecha),str(date_to_validate)),2)
        if date_similarity > dates_similarity:
                dates_similarity = date_similarity
                date_doc=fecha
                
    #print(dates_similarity)

    if dates_similarity >= 0.9:
        date_validated = 1
        print(f'DATE {date_to_validate} is VALIDATED')
    else:
        print(f'DATE {date_to_validate} is NOT VALIDATED')
        
        
    # ID Validation

    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('.', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace(',', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace(':', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('-', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('no', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('n°', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('  ', " ")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('   ', " ")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('numero', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('no.', "")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('cc', "cedula de ciudadania")
    id_extracted_df['id_extracted']=id_extracted_df['id_extracted'].str.replace('doc', "cedula de ciudadania")
    #id_extracted_df['id_extracted']     
    
    id_extracted_list=id_extracted_df['id_extracted'].unique()
    id_extracted_list=id_extracted_list.tolist()
    id_extracted_list
    
    id_type_to_validate=df.iloc[:,1].to_numpy()[0]
    #id_type_to_validate
    
    id_number_to_validate=df.iloc[:,2].to_numpy()[0]
    #id_number_to_validate
    
    id_number_to_validate=id_number_to_validate.replace('.', "")
    id_number_to_validate=id_number_to_validate.replace('-', "")
    
    id_to_validate = id_type_to_validate + ' ' + id_number_to_validate
    id_to_validate
    
    # Validating ID
    id_validated = 0
    ids_similarity = 0.0
    id_doc=str(object='')

    for id in id_extracted_list:
        id_similarity = round(similar(str(id),str(id_to_validate)),2)
        if id_similarity > ids_similarity:
                ids_similarity = id_similarity
                id_doc=id 
    
    ids_similarity
    
    if ids_similarity >= 0.9:
        id_validated = 1
        print(f'ID {id_to_validate} is VALIDATED')
    else:
        #ids_doc = ' '.join(word for word in no_id_doc.split()[0:1])
        print(f'ID {id_to_validate} is NOT VALIDATED')
        
    docs_list=id_doc.split()
    #docs_list    
    
    doc_type = []
    doc_number = []
    for item in docs_list:
        if item.isdecimal():
            doc_number.append(item)
        else:
            doc_type.append(item)
            
    doc_type= ' '.join(word for word in doc_type)
    doc_number= ' '.join(word for word in doc_number)    
    
    id_type_similarity = round(similar(str(doc_type),str(id_type_to_validate)),2)
    id_number_similarity = round(similar(str(doc_number),str(id_number_to_validate)),2)
    
    
    # NAME Validation
    
    person_extracted_list=person_extracted_df['person_extracted'].unique()
    person_extracted_list=person_extracted_list.tolist()
    person_extracted_list
    
    name_to_validate=df.iloc[:,3].to_numpy()[0]
    name_to_validate
    
    name_to_validate_list = name_to_validate.split()
    name_to_validate_list
    
    # Validating name
    name_validated = 0
    nombres = []
    no_nombres = []
    for nombre in name_to_validate_list:
        for persona in person_extracted_list:
            if nombre == persona:
                nombres.append(nombre)
            else:
                no_nombres.append(persona)
    
    name_doc = ' '.join(word for word in nombres)
    name_doc
    
    no_name_doc = ' '.join(word for word in no_nombres)
    no_name_doc
    
    name_similarity = round(similar(name_doc,name_to_validate),2)
    name_similarity
    
    if name_similarity >= 0.8:
        name_validated = 1
        nombre_doc = name_doc
        print(f'PERSON {name_to_validate} is VALIDATED')
    else:
        nombre_doc = ' '.join(word for word in no_name_doc.split()[0:4])
        print(f'PERSON {name_to_validate} is NOT VALIDATED')
        
    # MONEY Validation

    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace('$', "")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace("  ", " ")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.replace("   ", " ")
    money_extracted_df['money_extracted']=money_extracted_df['money_extracted'].str.lstrip()
    money_extracted_df['money_extracted']
        
    def money_format(money_figure):
    
        money_extracted_list = money_figure.split('.')
        #print(money_extracted_list) 
        element_list=[]
        for element in money_extracted_list:
            sublist=element.split(',')
            element_list.append(sublist)

        flat_element_list = [item for sublist in element_list for item in sublist]
        #print(flat_element_list)
        
        if (len(flat_element_list[-1])==1) | (len(flat_element_list[-1])==2):
            quantity=' '.join(number for number in flat_element_list[:-1])
            #print(f'm {quantity}')
            quantity=quantity.replace(" ", "")
            #print(f'n {quantity}')
            quantity=quantity+'.'+ flat_element_list[-1]
            #print(f'o {quantity}')
            quantity="${:,.2f}".format(float(quantity))
            #print(f'p {quantity}') 

        else:
            quantity=' '.join(number for number in flat_element_list)
            #print(f'A {quantity}')
            quantity=quantity.replace(" ", "")
            #print(f'B {quantity}')
            quantity=quantity+'.00'
            #print(f'C {quantity}')
            quantity="${:,.2f}".format(float(quantity))
            #print(f'D {quantity}')
        
        return quantity
    
    money_extracted_list=money_extracted_df['money_extracted'].apply(lambda x: money_format(x))
    money_extracted_list
    
    money_extracted_set = set(money_extracted_list)
    money_extracted_set
    
    money_to_validate=df.iloc[:,5].to_numpy()[0]
    money_to_validate
    
    money_add_to_validate=df.iloc[:,6].to_numpy()[0]
    money_add_to_validate
    
    #round(money_to_validate,2)
    money_to_validate="${:,.2f}".format(money_to_validate)
    money_to_validate
    
    #round(money_add_to_validate,2)
    money_add_to_validate="${:,.2f}".format(money_add_to_validate)
    money_add_to_validate
    
    # Validating MONEY
    money_validated = 0
    moneys_similarity = 0.0
    money_doc=str(object='')

    for figure in money_extracted_set:
        money_similarity = round(similar(str(figure),str(money_to_validate)),2)
        if money_similarity > moneys_similarity:
                moneys_similarity = money_similarity
                money_doc=figure
                            
    # Validating MONEY ADD
    money_add_validated = 0
    moneys_add_similarity = 0.0
    money_add_doc=str(object='')

    for figure in money_extracted_set:
        money_add_similarity = round(similar(str(figure),str(money_add_to_validate)),2)
        if money_add_similarity > moneys_add_similarity:
                moneys_add_similarity = money_add_similarity
                money_add_doc=figure
                
    moneys_similarity
    
    moneys_add_similarity
    
    if moneys_similarity >= 0.9:
        money_validated = 1
        print(f'MONEY {money_to_validate} is VALIDATED')
    else:
        print(f'MONEY {money_to_validate} is NOT VALIDATED')
    
    
    if moneys_add_similarity >= 0.9:
        money_add_validated = 1
        print(f'MONEY ADD {money_add_to_validate} is VALIDATED')
    else:
        print(f'MONEY ADD {money_add_to_validate} is NOT VALIDATED')
        
    # ORGANIZATION Validation

    org_extracted_list=org_extracted_df['org_extracted'].unique()
    org_extracted_list=org_extracted_list.tolist()
    org_extracted_list
    
    org_extracted_list=org_extracted_df['org_extracted'].apply(lambda x: x.split())
    flat_org_extracted_list = [item for sublist in org_extracted_list for item in sublist]
    org_extracted_set = set(flat_org_extracted_list)
    org_extracted_set
    
    org_to_validate=df.iloc[:,7].to_numpy()[0]
    org_to_validate
    
    org_to_validate=org_to_validate.replace('-', "")
    org_to_validate
    
    org_to_validate_list = org_to_validate.split()
    org_to_validate_list
    
    # Validating organization
    org_validated = 0
    orgs = []
    no_orgs = []
    for entidad in org_to_validate_list:
        for org in org_extracted_set:
            if entidad == org:
                orgs.append(entidad)
            else:
                no_orgs.append(org)    

    org_doc = ' '.join(word for word in orgs)
    org_doc  

    no_org_doc = ' '.join(word for word in no_orgs)
    no_org_doc    
    
    org_similarity = round(similar(org_doc,org_to_validate),2)
    org_similarity
    
    if org_similarity >= 0.8:
        org_validated = 1
        orga_doc = org_doc
        print(f'ORGANIZATION {org_to_validate} is VALIDATED')
    else:
        orga_doc = ' '.join(word for word in no_org_doc.split()[0:4])
        print(f'ORGANIZATION {org_to_validate} is NOT VALIDATED')
    
    #Calculating Validation Score
    
    number_of_variables = 7
    validation_score = (org_similarity + 
                    moneys_similarity + 
                    moneys_add_similarity +
                    id_type_similarity + 
                    id_number_similarity +
                    name_similarity + 
                    dates_similarity)/ number_of_variables

    if validation_score >= 0.9:
        contract_validation_status = 'GREEN'
    elif validation_score > 0.6:
        contract_validation_status = 'YELLOW'
    else:
        contract_validation_status = 'RED'

    print('VALIDATION REPORT')
    print('---------------------------------------------')
    print(f'Validation score is:     {round(validation_score,2)}, contract validation status is:   {contract_validation_status}.')
    print('')
    print('Entity,                   ( Database,        Document,        Similarity)')
    print(f'Date similarity is:      {date_to_validate, date_doc, dates_similarity}')
    print(f'Name similarity is:      {name_to_validate, nombre_doc, name_similarity}')
    print(f'Id type similarity is:   {id_type_to_validate, doc_type, id_type_similarity}')
    print(f'Id number similarity is: {id_number_to_validate, doc_number, id_number_similarity}')
    print(f'Money similarity is:     {money_to_validate, money_doc, moneys_similarity}')
    print(f'Money add similarity is: {money_add_to_validate, money_add_doc, moneys_add_similarity}')
    print(f'Entity similarity is:    {org_to_validate, orga_doc, org_similarity}')
    print('---------------------------------------------')
    print('')
    
    import psycopg2 as ps
    
    host = 'ds4a-demo-instance.cwmtqeffz1wh.us-east-2.rds.amazonaws.com'
    port = 5432
    user = 'team_34_user'
    password = 'team34'
    database = 'project_team_34_db'
    
    try:
        connection = ps.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)
        cursor = connection.cursor()

        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 7, date_to_validate, date_doc, dates_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 4, name_to_validate, nombre_doc, name_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 5, id_type_to_validate, doc_type, id_type_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 6, id_number_to_validate, doc_number, id_number_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 9, money_to_validate, money_doc, moneys_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 10, money_add_to_validate, money_add_doc, moneys_add_similarity))
        cursor.execute("INSERT INTO doc_validados (uuid, fechaevaluacion, tipocampo, valorbd, valordoc, coincidencia) VALUES (%s,%s,%s,%s,%s,%s)", ( uid, '2020-11-09', 1, org_to_validate, orga_doc, org_similarity))

        cursor.execute("UPDATE doc_contrato SET procesado = %s WHERE uuid = %s", (1, uid))

        connection.commit()
        count = cursor.rowcount
        print (count, "Record inserted successfully into doc_validados table")

    except (Exception, ps.Error) as error :
        if(connection):
            print("Failed to insert record into mobile table", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        
        
    return validation_score
   
