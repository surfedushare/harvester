import { formatDate, generateSearchMaterialsQuery } from "../../_helpers";
import { isEmpty, isError, isNil, isObject } from "lodash";

import AddCollection from "./../../Popup/AddCollection";
import { Duration } from "luxon";
import EnlargeableImage from "@diracleo/vue-enlargeable-image";
import Multiselect from "./../../Multiselect";
import SaveMaterialInCollection from "./../../Popup/SaveMaterialInCollection";
import SelectDownloadPopup from "@/components/Popup/SelectDownload/SelectDownload";
import ShareMaterial from "~/components/Popup/ShareMaterial";
import { mapGetters } from "vuex";
import { validateHREF } from "~/components/_helpers";

export default {
  name: "sidebar",
  dependencies: ["$log"],
  props: {
    material: {
      type: Object,
      default: null,
    },
    collections: {
      type: Array,
      default: [],
    },
  },
  components: {
    SaveMaterialInCollection,
    AddCollection,
    ShareMaterial,
    Multiselect,
    SelectDownloadPopup,
    EnlargeableImage,
  },
  mounted() {
    this.setSocialCounters();
    this.href = validateHREF(window.location.href);
  },
  data() {
    return {
      href: "",
      currentCollectionIds: this.collections.map((c) => c.id),
      submitting: false,
      isShowSaveMaterial: false,
      isShowShareMaterial: false,
      isShowAddCollection: false,
      showDownloadPopup: false,
      socialCounterInterval: null,
    };
  },
  methods: {
    toggleDownloadPopup() {
      this.showDownloadPopup = !this.showDownloadPopup;
    },
    getIdeaLink(idea) {
      const query = generateSearchMaterialsQuery({
        search_text: '"' + idea + '"',
        filters: [],
      });
      const route = this.$router.resolve(query);
      return route.href;
    },
    /**
     * generate login URL
     * @returns {string}
     */
    getLoginLink() {
      return this.$store.getters.getLoginLink(this.$route);
    },
    /**
     * Show AddCollection popup
     */
    addCollection() {
      this.isShowAddCollection = true;
    },
    /**
     * Close AddCollection popup
     */
    closeAddCollection() {
      this.isShowAddCollection = false;
    },
    /**
     * Close SaveMaterial popup
     */
    closeSaveMaterial() {
      this.isShowSaveMaterial = false;
    },
    addToCollection(collectionId) {
      this.submitting = true;

      return this.$store
        .dispatch("addMaterialToCollection", {
          collection_id: collectionId,
          data: [
            {
              external_id: this.material.external_id,
              position: this.collectionItems.length,
            },
          ],
        })
        .then(() => (this.submitting = false));
    },
    /**
     * Triggering event the remove material
     */
    removeFromCollection(collectionId) {
      this.submitting = true;

      return this.$store
        .dispatch("removeMaterialFromCollection", {
          collection_id: collectionId,
          data: [
            {
              external_id: this.material.external_id,
            },
          ],
        })
        .then(() => (this.submitting = false));
    },
    /**
     * generate copyright external link
     * @param copyright
     * @returns {string}
     */
    copyrightURL(copyright) {
      let str = "";

      switch (copyright) {
        case "cc-by-30":
          str = `https://creativecommons.org/licenses/by/3.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by":
        case "cc-by-40":
          str = `https://creativecommons.org/licenses/by/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nc":
        case "cc-by-nc-40":
          str = `https://creativecommons.org/licenses/by-nc/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nc-30":
          str = `https://creativecommons.org/licenses/by-nc/3.0/deed.${this.$i18n.locale}`;
          break;
        case "yes":
        case "cc-by-nc-nd":
        case "cc-by-nc-nd-40":
          str = `https://creativecommons.org/licenses/by-nc-nd/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nc-nd-30":
          str = `https://creativecommons.org/licenses/by-nc-nd/3.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nc-sa":
        case "cc-by-nc-sa-40":
          str = `https://creativecommons.org/licenses/by-nc-sa/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nc-sa-30":
          str = `https://creativecommons.org/licenses/by-nc-sa/3.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nd":
        case "cc-by-nd-40":
          str = `https://creativecommons.org/licenses/by-nd/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-nd-30":
          str = `https://creativecommons.org/licenses/by-nd/3.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-sa":
        case "cc-by-sa-40":
          str = `https://creativecommons.org/licenses/by-sa/4.0/deed.${this.$i18n.locale}`;
          break;
        case "cc-by-sa-30":
          str = `https://creativecommons.org/licenses/by-sa/3.0/deed.${this.$i18n.locale}`;
          break;
        case "cc0-10":
          str = `https://creativecommons.org/publicdomain/zero/1.0/deed.${this.$i18n.locale}`;
          break;
        case "pdm-10":
          str =
            this.$i18n.locale === "nl"
              ? "https://creativecommons.nl/publiek-domein/"
              : "https://creativecommons.org/share-your-work/public-domain/pdm/";
          break;
        default:
          str = "https://creativecommons.org/licenses/";
          break;
      }

      return str;
    },

    /**
     * Show the popup "Share rating"
     */
    showShareMaterial() {
      this.isShowShareMaterial = true;
    },

    /**
     * Close the popup "Share rating"
     */
    closeShareMaterial() {
      this.isShowShareMaterial = false;
      if (this.is_copied) {
        this.closeSocialSharing("link");
      }
    },

    /**
     * Set counters value for share buttons
     */
    setSocialCounters() {
      this.socialCounterInterval = setInterval(() => {
        this.$nextTick().then(() => {
          const { material } = this;
          const { social_counters } = this.$refs;
          // Somehow the $refs can be empty when this method runs, but it rarely happens.
          // When it does (on the homepage for mysterious reasons) the page seems to get stuck in a loop
          // We'll throw an error and see if Sentry sends some information to reproduce the problem.
          if (!social_counters) {
            throw new Error("Problems with social counter");
          }
          const linkedIn = social_counters.querySelector("#linkedin_counter");

          if (material && material.sharing_counters && linkedIn) {
            const share = material.sharing_counters.reduce(
              (prev, next) => {
                prev[next.sharing_type] = next;
                return prev;
              },
              {
                linkedin: {
                  counter_value: 0,
                },
                twitter: {
                  counter_value: 0,
                },
                link: {
                  counter_value: 0,
                },
              }
            );

            if (share.linkedin) {
              linkedIn.innerText = share.linkedin.counter_value;
            }
            if (share.twitter) {
              social_counters.querySelector("#twitter_counter").innerText =
                share.twitter.counter_value;
            }
            if (share.link) {
              social_counters.querySelector("#url_counter").innerText =
                share.link.counter_value;
            }
            if (linkedIn) {
              clearInterval(this.socialCounterInterval);
            }
          }
        });
      }, 3500);
    },

    /**
     * Event close social popups
     * @param type - String - social type
     */
    closeSocialSharing(type) {
      /** This block prevents the user from sharing a material multiple times */
      if (type === "linkedin") {
        if (this.linkedin_shared === true) {
          return;
        }
        this.linkedin_shared = true;
      }
      if (type === "twitter") {
        if (this.twitter_shared === true) {
          return;
        }
        this.twitter_shared = true;
      }
      if (type === "link") {
        if (this.link_shared === true) {
          return;
        }
        this.link_shared = true;
      }

      this.$store
        .dispatch("setMaterialSocial", {
          id: this.$route.params.id,
          params: {
            shared: type,
          },
        })
        .then(() => {
          this.setSocialCounters();
        });
    },
    getTitleTranslation(item, language) {
      if (!isEmpty(item.title_translations)) {
        return item.title_translations[language];
      }
      return item.name;
    },
    downloadOnClick(event, material) {
      const dimensions = material.publishers.length
        ? { dimension3: material.publishers.join(" - ") }
        : {};
      this.$log.customEvent(
        "Goal",
        "Download",
        event.currentTarget.href,
        null,
        dimensions
      );
      if (!material.files || material.files.length <= 1) {
        return;
      }
      // Dealing with a multi file scenario. We'll open the modal instead of navigating away.
      event.preventDefault();
      this.showDownloadPopup = true;
    },
    parseVideoDuration(duration) {
      return Duration.fromISO(duration).toFormat("h:mm:ss").padStart(8, "0");
    },
    shouldShowPreviews() {
      return !isEmpty(this.material.previews);
    },
  },
  computed: {
    ...mapGetters([
      "isAuthenticated",
      "my_collections",
      "material_communities",
      "disciplines",
    ]),
    formattedPublishedAt() {
      return formatDate(this.material.published_at, this.$i18n.locale);
    },
    collectionItems() {
      return this.my_collections.map((collection) => {
        const collectionTitle = collection[`title_${this.$i18n.locale}`];
        const communityTitles = collection.communities.map((community) => {
          const communityDetails = community.community_details.find(
            (details) => {
              return details.language_code.toLowerCase() === this.$i18n.locale;
            }
          );
          return communityDetails.title;
        });
        return {
          id: collection.id,
          title: `${collectionTitle} (${communityTitles.join(" ,")})`,
        };
      });
    },
    /**
     * Extend to the material fields "disciplines"
     * @returns {*}
     */
    extended_material() {
      const { material, disciplines } = this;
      let self = this;

      if (isNil(material) || isError(material)) {
        return material;
      }

      if (!isNil(disciplines)) {
        // TODO: material.disciplines is sometimes an Array with Object and sometimes with external_id
        // We should make the type consistent
        let disciplineTitles = material.disciplines.map((discipline) => {
          let disciplineObj = isObject(discipline)
            ? discipline
            : disciplines[discipline];
          return this.getTitleTranslation(disciplineObj, self.$i18n.locale);
        });
        material.disciplineTitles = disciplineTitles.join(", ");
      }

      return material;
    },
  },
  watch: {
    collections() {
      this.currentCollectionIds = this.collections.map((c) => c.id);
    },
  },
  beforeDestroy() {
    clearInterval(this.socialCounterInterval);
  },
};
