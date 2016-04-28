(ns extract-species.core
	(:require [clojure.data.xml :as xml]))

(def params #{:EF_MONOS :EF_MONO :EF_ISO
							:THETA :FAGE
							:CT_IS :CT_MT
							:HA_IS :HA_MT
							:DS_IS :DS_MT
							:HD_IS :HD_MT})

(defn get-species-params
	[{:keys [attrs content]}]
	{:short (:mnemonic attrs)
	 :long (:name attrs)
	 :params (into {}
								 (for [{:keys [tag attrs]} content]
									 (when (= tag :par)
										 (let [n (:name attrs)]
											 (when ((keyword n) params)
												 [n (:value attrs)])))))})

(defn parse-species
	[{:keys [attrs content]}]
	(remove nil?
					(for [{:keys [tag attrs content] :as s} content]
						(when (= tag :species)
							(let [m (assoc (get-species-params s)
												:specifics (remove nil? (when (seq content)
																									(parse-species s))))]
								(when (or (seq (:params m))
													(seq (:specifics m)))
									m))))))

(defn parse-file
	[]
	(let [f (slurp "C:\\Users\\berg\\Documents\\development\\ldndc\\ldndc-dev_debug\\resources\\parameters-species.xml")
				sr (java.io.StringReader. f)
				p (xml/parse sr)]
		(-> p :content first parse-species)))